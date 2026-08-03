# -*- coding: utf-8 -*- #
# Copyright 2026 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""`gcloud dataplex dbt metadata-jobs create` command."""

from __future__ import annotations

import os

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.dataplex import dbt_metadata_job as dbt_job_lib
from googlecloudsdk.api_lib.dataplex import entry_group as entry_group_lib
from googlecloudsdk.api_lib.dataplex import metadata_job as metadata_job_lib
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.dataplex.dbt import bigquery_location as bq_loc
from googlecloudsdk.command_lib.dataplex.dbt import profiles as dbt_profiles
from googlecloudsdk.command_lib.dataplex.dbt import transform as dbt_transform
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files

_JSONL_FILENAME = 'dbt_metadata.jsonl'


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Transform dbt-core artifacts and import them into Dataplex Catalog.

  This command reads the JSON artifacts produced by dbt-core (manifest.json,
  catalog.json, run_results.json, sources.json) from a local directory,
  transforms them into the Dataplex metadata import format, uploads the result
  to Cloud Storage, and triggers a Dataplex metadata import job that ingests
  the metadata into the Knowledge Catalog.

  Only the entry group that receives the dbt entries must exist in the caller's
  project beforehand. The caller must also be able to USE the dbt connector
  types (dataplex.aspectTypes.use / the dbt-connector-types alternate-use
  permission).

  The Metadata Job ID identifies the import run and, if provided, must:
   * Contain only lowercase letters, numbers, and hyphens.
   * Start with a letter and end with a number or a letter.
   * Be 1-63 characters and unique within the project / location.
  """

  detailed_help = {
      'EXAMPLES': (
          """\
          To transform the dbt artifacts in the current directory and import
          them into entry group `dbt-metadata-ingestion` in project
          `my-project`, location `us-central1`, run:

            $ {command} my-dbt-import --project=my-project \
                --location=us-central1 \
                --artifacts-path=. \
                --entry-group=dbt-metadata-ingestion \
                --storage-uri=gs://my-bucket/dbt-imports/

          To only build and upload the JSONL and validate the job without
          ingesting, add `--validate-only`.
          """
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    resource_args.AddMetadataJobResourceArg(parser, 'to create.')
    parser.add_argument(
        '--artifacts-path',
        default='.',
        help="""Local path to the dbt-core artifacts. May point at the dbt
        project root (the `target/` subdirectory is detected automatically) or
        directly at the directory containing manifest.json. Defaults to the
        current working directory.""",
    )
    parser.add_argument(
        '--storage-uri',
        required=True,
        help="""Cloud Storage URI prefix (gs://bucket/path/) the transformed
        JSONL is uploaded to and the import job reads from. The caller must have
        write access and the Dataplex service agent must have read access.""",
    )
    parser.add_argument(
        '--entry-group',
        default='dbt-metadata-ingestion',
        help="""Short ID of the entry group that receives the dbt entries. Must
        already exist in the project / location.""",
    )
    parser.add_argument(
        '--connector-types-project',
        hidden=True,
        help="""Overrides the project that owns the 1P dbt aspect/entry types.
        Defaults automatically; for internal/testing use only.""",
    )
    parser.add_argument(
        '--system-types-project',
        hidden=True,
        help="""Overrides the project that owns the core 1P types the dbt types
        depend on (the `contacts` aspect type and the dbt entry link types).
        Defaults automatically; for internal/testing use only.""",
    )
    parser.add_argument(
        '--import-entry-sync-mode',
        choices={
            'FULL': (
                """All entries in the job scope are synced; entries absent
                    from the import file are deleted."""
            ),
            'INCREMENTAL': (
                """Only entries present in the import file are
                    modified."""
            ),
        },
        type=arg_utils.ChoiceToEnumName,
        default='FULL',
        help='Entry sync mode for the import job.',
    )
    parser.add_argument(
        '--import-aspect-sync-mode',
        choices={
            'FULL': """All aspects in the job scope are synced.""",
            'INCREMENTAL': (
                """Only aspects present in the import file are
                    modified."""
            ),
        },
        type=arg_utils.ChoiceToEnumName,
        default='INCREMENTAL',
        help='Aspect sync mode for the import job.',
    )
    parser.add_argument(
        '--include-entry-links',
        action='store_true',
        default=True,
        help="""Also emit EntryLink records capturing dbt lineage and semantic
        relationships (depends-on, belongs-to, consumed-by, etc.).""",
    )
    bigquery_link_group = parser.add_group(
        mutex=True,
        help="""Control `materializes-to` links from materialized dbt nodes to
        their physical BigQuery table entries.""",
    )
    bigquery_link_group.add_argument(
        '--bigquery-location',
        help="""Dataplex region of the physical BigQuery table entries (the
        system `@bigquery` entry group), e.g. `us-central1`. Used to emit
        `materializes-to` links from each materialized dbt node
        (model/seed/snapshot) to its physical BigQuery table entry. If omitted,
        it is inferred from the dbt project's `profiles.yml`
        (`outputs.<target>.location`); when it cannot be inferred, either pass
        this flag or `--skip-bigquery-link`.""",
    )
    bigquery_link_group.add_argument(
        '--skip-bigquery-link',
        action='store_true',
        default=False,
        help="""Skip `materializes-to` links (dbt node -> physical BigQuery
        table). Use when the BigQuery tables are not cataloged in Dataplex or
        the location cannot be provided.""",
    )
    bigquery_link_group.add_argument(
        '--skip-bigquery-location-lookup',
        action='store_true',
        default=False,
        help="""Do not call BigQuery to read the materialized datasets' actual
        locations; infer the location from the dbt project's `profiles.yml`
        instead. Use offline, without `bigquery.datasets.get` access, or to
        avoid the extra API calls.""",
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help="""Build and upload the JSONL and validate the metadata job, but
        don't actually ingest.""",
    )
    base.ASYNC_FLAG.AddToParser(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args: parser_extensions.Namespace) -> None:
    metadata_job = args.CONCEPTS.metadata_job.Parse()
    parent = metadata_job.Parent().RelativeName()
    project_id = metadata_job.projectsId
    location = metadata_job.locationsId
    metadata_job_id = self._GetMetadataJobId(metadata_job)

    # Entry names / entry-group refs use the project NUMBER.
    project_number = self._GetProjectNumber(project_id)

    # The 1P dbt types live in env-specific system projects at `global`:
    # dbt aspect/entry types in the connector project, contacts + entry link
    # types in the core system project.
    connector_types_project = dbt_job_lib.ResolveConnectorTypesProject(
        args.connector_types_project
    )
    system_types_project = dbt_job_lib.ResolveSystemTypesProject(
        args.system_types_project
    )
    # The 1P dbt types always live at the `global` location.
    types_location = 'global'
    log.status.Print(
        'Using dbt types from [{0}] and core types from [{1}] (location {2}).'
        .format(connector_types_project, system_types_project, types_location)
    )

    # Fail fast if the target entry group is missing, before spending time
    # transforming artifacts and uploading them to GCS (otherwise this surfaces
    # only later, in the asynchronous import job).
    self._CheckEntryGroupExists(
        project_number, project_id, location, args.entry_group
    )

    # Resolve the BigQuery location for materializes-to links (dbt node ->
    # physical @bigquery table). Not in the dbt artifacts, so: flag wins, else
    # infer from the project's profiles.yml, else require the caller to pass it
    # or opt out with --skip-bigquery-link.
    bigquery_location = self._ResolveBigQueryLocation(args)

    # 1. Transform dbt artifacts into a JSONL import file in a temp dir.
    with files.TemporaryDirectory() as tmp_dir:
      local_jsonl = os.path.join(tmp_dir, _JSONL_FILENAME)
      summary = dbt_transform.GenerateImportFile(
          artifacts_path=args.artifacts_path,
          output_path=local_jsonl,
          eg_project=project_number,
          eg_location=location,
          entry_group=args.entry_group,
          connector_types_project=connector_types_project,
          system_types_project=system_types_project,
          types_location=types_location,
          include_entry_links=args.include_entry_links,
          bigquery_location=bigquery_location,
      )
      log.status.Print(
          'Transformed dbt artifacts: {0} entries, {1} entry links.'.format(
              summary['entries'], summary['entry_links']
          )
      )

      # 2. Upload the JSONL under a per-job prefix (avoids stale-file
      #    duplicates) and point the import job at that prefix.
      storage_prefix = self._JobStoragePrefix(args.storage_uri, metadata_job_id)
      object_uri = storage_prefix + _JSONL_FILENAME
      log.status.Print('Uploading import file to {0} ...'.format(object_uri))
      storage_api.StorageClient().CopyFileToGCS(
          local_jsonl, storage_util.ObjectReference.FromUrl(object_uri)
      )

    # 3. Build and submit the import job referencing the dbt connector types.
    entry_link_types = None
    referenced_entry_scopes = None
    extra_aspect_types = None
    if args.include_entry_links:
      entry_link_types = dbt_transform.LinkTypeFqns(
          system_types_project, types_location
      )
      # Scope the caller's project plus any BigQuery projects that
      # materializes-to links target, so those cross-entry references resolve.
      referenced_entry_scopes = ['projects/{0}'.format(project_number)] + [
          'projects/{0}'.format(p)
          for p in summary.get('bigquery_projects', [])
      ]
      # logical-schema-join links (from dbt relationships tests) carry a
      # `schema-join` aspect -- a core 1P type in the system project; it must be
      # in the import scope for the aspect to be accepted.
      extra_aspect_types = [
          'projects/{0}/locations/{1}/aspectTypes/schema-join'.format(
              system_types_project, types_location
          )
      ]

    job = dbt_job_lib.GenerateImportMetadataJob(
        eg_project=project_number,
        eg_location=location,
        entry_group=args.entry_group,
        connector_types_project=connector_types_project,
        system_types_project=system_types_project,
        source_storage_uri=storage_prefix,
        entry_sync_mode=args.import_entry_sync_mode,
        aspect_sync_mode=args.import_aspect_sync_mode,
        entry_link_types=entry_link_types,
        referenced_entry_scopes=referenced_entry_scopes,
        extra_aspect_types=extra_aspect_types,
    )

    dataplex_client = dataplex_util.GetClientInstance()
    message = dataplex_util.GetMessageModule()
    create_req_op = dataplex_client.projects_locations_metadataJobs.Create(
        message.DataplexProjectsLocationsMetadataJobsCreateRequest(
            metadataJobId=metadata_job_id,
            parent=parent,
            googleCloudDataplexV1MetadataJob=job,
            validateOnly=args.validate_only,
        ),
    )

    if args.validate_only:
      log.status.Print('Validation complete.')
      return

    # Always surface the operation up front so the import job can be monitored
    # externally (e.g. `gcloud dataplex operations describe`), whether or not we
    # wait for it to finish.
    log.status.Print(
        'Submitted dbt metadata import job with operation [{0}].'.format(
            create_req_op.name
        )
    )

    if getattr(args, 'async_', False):
      return

    metadata_job_lib.WaitForOperation(create_req_op)
    log.CreatedResource(
        metadata_job_id,
        details='dbt metadata import job created in [{0}]'.format(parent),
    )

  def _ResolveBigQueryLocation(
      self, args: parser_extensions.Namespace
  ) -> str | None:
    """Resolves the Dataplex region of the physical @bigquery table entries.

    materializes-to links target those entries; their region is not in the dbt
    artifacts. Resolution order: skip flag -> None; explicit flag; the datasets'
    actual location via a live BigQuery lookup (authoritative); best-effort
    inference from the dbt project's profiles.yml; otherwise raise so the caller
    supplies it or opts out.

    Args:
      args: the parsed command arguments.

    Returns:
      The BigQuery location, or None when entry links / materializes-to links
      are not being emitted.

    Raises:
      RequiredArgumentException: when it cannot be resolved and neither
        --bigquery-location nor --skip-bigquery-link was given, or when the
        materialized datasets span multiple BigQuery regions.
    """
    if not args.include_entry_links or args.skip_bigquery_link:
      return None
    if args.bigquery_location:
      return args.bigquery_location
    # Authoritative: the datasets' own (immutable) locations.
    if not args.skip_bigquery_location_lookup:
      resolved = self._ResolveViaBigQuery(args.artifacts_path)
      if resolved:
        return resolved
    inferred = dbt_profiles.infer_bigquery_location(args.artifacts_path)
    if inferred:
      if inferred.source == dbt_profiles.SOURCE_DEFAULT:
        log.warning(
            'The dbt project sets no BigQuery location in profiles.yml; '
            'assuming the [{0}] multi-region (the dbt-bigquery default for new '
            'datasets) for materializes-to links. If the tables live in '
            'another region, pass --bigquery-location=REGION or '
            '--skip-bigquery-link.'.format(inferred.location)
        )
      else:
        log.status.Print(
            'Inferred BigQuery location [{0}] from the dbt project for '
            'materializes-to links.'.format(inferred.location)
        )
      return inferred.location
    raise calliope_exceptions.RequiredArgumentException(
        '--bigquery-location',
        'Could not determine the BigQuery location of the dbt resources -- '
        'neither from a live BigQuery lookup nor from the project '
        '(profiles.yml). Pass --bigquery-location=REGION (the Dataplex region '
        "of the physical BigQuery table entries, e.g. 'us-central1') to emit "
        'materializes-to links, or --skip-bigquery-link to skip them.',
    )

  def _ResolveViaBigQuery(self, artifacts_path: str) -> str | None:
    """Reads the shared region of the datasets the dbt run materializes into.

    Reads each materialized dataset's location with a live ``datasets.get``.

    Args:
      artifacts_path: the --artifacts-path value.

    Returns:
      The single Dataplex region shared by the materialized datasets, or None
      when there is nothing to materialize or no dataset could be read.

    Raises:
      RequiredArgumentException: when the materialized datasets span multiple
        BigQuery regions, which a single materializes-to location cannot
        represent.
    """
    datasets = dbt_transform.MaterializedBigQueryDatasets(artifacts_path)
    if not datasets:
      return None
    resolved = bq_loc.ResolveDatasetLocations(datasets)
    if not resolved:
      log.warning(
          'Could not read the materialized BigQuery datasets to determine '
          'their location (missing access or datasets); falling back to '
          "the dbt project's profiles.yml."
      )
      return None
    regions = set(resolved.values())
    if len(regions) == 1:
      region = next(iter(regions))
      log.status.Print(
          'Resolved BigQuery location [{0}] from the materialized datasets for '
          'materializes-to links.'.format(region)
      )
      return region
    raise calliope_exceptions.RequiredArgumentException(
        '--bigquery-location',
        'The dbt project materializes tables into BigQuery datasets in more '
        'than one region ({0}), which a single materializes-to location cannot '
        'represent. Pass --bigquery-location=REGION to pin one, or '
        '--skip-bigquery-link to skip these links.'.format(
            ', '.join(sorted(regions))
        ),
    )

  def _CheckEntryGroupExists(
      self,
      project_number: str,
      project_id: str,
      location: str,
      entry_group: str,
  ) -> None:
    """Fails early with an actionable message if the entry group is absent.

    Only a genuine "not found" is treated as fatal here; any other error (e.g. a
    transient failure, or a permission check that Get is stricter about than the
    import job) is left to surface later rather than blocking the import on a
    best-effort pre-flight check.

    Args:
      project_number: project NUMBER owning the entry group (used in the name).
      project_id: project ID, for the actionable error message.
      location: Dataplex region of the entry group.
      entry_group: short id of the entry group.

    Raises:
      exceptions.Error: if the entry group does not exist.
    """
    name = 'projects/{0}/locations/{1}/entryGroups/{2}'.format(
        project_number, location, entry_group
    )
    try:
      entry_group_lib.GetEntryGroup(name)
    except apitools_exceptions.HttpNotFoundError as exc:
      raise exceptions.Error(
          'Entry group [{entry_group}] does not exist in project '
          '[{project_id}], location [{location}]. Create it first, e.g.:\n'
          '  gcloud dataplex entry-groups create {entry_group} '
          '--project={project_id} --location={location}\n'
          'then re-run this command.'.format(
              entry_group=entry_group,
              project_id=project_id,
              location=location,
          )
      ) from exc
    except apitools_exceptions.HttpError as exc:
      log.debug(
          'Ignoring non-404 error from entry group pre-flight check: %s', exc
      )

  def _GetMetadataJobId(self, metadata_job: resources.Resource) -> str | None:
    metadata_job_id = metadata_job.RelativeName().split('/')[-1]
    if metadata_job_id == resource_args.GENERATE_ID:
      return None
    return metadata_job_id

  def _GetProjectNumber(self, project_id: str) -> str:
    project_ref = projects_util.ParseProject(project_id)
    return str(projects_api.Get(project_ref).projectNumber)

  def _JobStoragePrefix(
      self, storage_uri: str, metadata_job_id: str | None
  ) -> str:
    """Returns gs://bucket/<prefix>/<job-id>/ for the per-job upload."""
    prefix = storage_uri if storage_uri.endswith('/') else storage_uri + '/'
    # When the job id is server-generated, fall back to a stable folder.
    job_folder = metadata_job_id or 'dbt-import'
    return '{0}{1}/'.format(prefix, job_folder)
