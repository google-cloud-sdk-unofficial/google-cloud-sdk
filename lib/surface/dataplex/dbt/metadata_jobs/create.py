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
import textwrap
import uuid

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.dataplex import dbt_metadata_job as dbt_job_lib
from googlecloudsdk.api_lib.dataplex import entry_group as entry_group_lib
from googlecloudsdk.api_lib.dataplex import metadata_job as metadata_job_lib
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.dataplex.dbt import artifacts as dbt_artifacts
from googlecloudsdk.command_lib.dataplex.dbt import bigquery_location as bq_loc
from googlecloudsdk.command_lib.dataplex.dbt import transform as dbt_transform
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files

_JSONL_FILENAME = 'dbt_metadata.jsonl'

# Metadata job states that mean the import is no longer running.
_TERMINAL_STATES = frozenset(
    ['SUCCEEDED', 'SUCCEEDED_WITH_ERRORS', 'FAILED', 'CANCELED']
)


def _HttpErrorSummary(error: apitools_exceptions.HttpError) -> str:
  """Describes an HttpError for a log line, tolerating a malformed response.

  ``HttpError.status_code`` subscripts the raw response, so it raises rather
  than returning anything when the response is absent or unparsed. This is only
  ever called from an error path, where raising would replace the real problem
  with a spurious one.

  Args:
    error: the HttpError to describe.

  Returns:
    'HTTP <code>', or 'error' when the code cannot be read.
  """
  try:
    return 'HTTP {0}'.format(error.status_code)
  except (AttributeError, KeyError, TypeError, ValueError):
    return 'error'


class _ImportJobPoller(waiter.OperationPoller):
  """Polls a metadata import job until it reaches a terminal state.

  The metadataJobs.create operation completes when the job is accepted, not when
  the import finishes, so the job's own status has to be polled to learn the
  real outcome (and entry counts).
  """

  def __init__(self, jobs_service, messages):
    self._jobs_service = jobs_service
    self._messages = messages

  def IsDone(self, job):
    state = job.status.state if job and job.status else None
    return str(state) in _TERMINAL_STATES if state else False

  def Poll(self, job_name):
    return self._jobs_service.Get(
        self._messages.DataplexProjectsLocationsMetadataJobsGetRequest(
            name=job_name
        )
    )

  def GetResult(self, job):
    return job


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Transform dbt-core artifacts and import them into Dataplex Catalog.

  This command reads the JSON artifacts produced by dbt-core (manifest.json,
  catalog.json, run_results.json, sources.json) from a local directory or a
  Cloud Storage folder, transforms them into the Dataplex metadata import
  format, uploads the result to Cloud Storage, and triggers a Dataplex metadata
  import job that ingests the metadata into the Knowledge Catalog.

  Only the entry group that receives the dbt entries must exist in the caller's
  project beforehand. The caller must also be able to USE the dbt connector
  types (dataplex.aspectTypes.use / the dbt-connector-types alternate-use
  permission).

  Unless `--aspects-only` is passed, the import is a FULL sync of the dbt
  contents of the entry group: any dbt entry in the entry group that this run's
  artifacts do not describe is DELETED. Give each dbt project its own entry
  group. Two dbt projects importing their own artifacts into one shared entry
  group will each delete the other's entries on every run.

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

          The artifacts may also be read from Cloud Storage, e.g. when they are
          published there by a dbt CI job:

            $ {command} my-dbt-import --project=my-project \
                --location=us-central1 \
                --artifacts-path=gs://my-bucket/dbt-artifacts/ \
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
        dbt_artifacts.ARTIFACTS_PATH_FLAG,
        default='.',
        help="""Path to the dbt-core artifacts: a local directory, or a Cloud
        Storage folder (`gs://bucket/folder/`) they were published to. May point
        at the dbt project root (the `target/` subdirectory is detected
        automatically) or directly at the directory containing manifest.json.
        manifest.json is required; catalog.json, run_results.json and
        sources.json are read if present. Defaults to the current working
        directory.""",
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
        already exist in the project / location. Use a separate entry group per
        dbt project: without `--aspects-only`, a run deletes the dbt entries in
        this entry group that its own artifacts do not describe.""",
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
        '--aspects-only',
        action='store_true',
        default=False,
        help=textwrap.dedent("""\
            Update only the metadata this dbt run observed, and leave the rest
            of the entry group untouched. No entry is created, deleted or
            re-parented, no entry link is emitted, and an aspect whose dbt
            artifact was absent from this run keeps the value a previous run
            gave it.

            Use this for routine ingestion, after whichever dbt command your
            pipeline already runs: `dbt build`, `dbt test`, `dbt source
            freshness`, or a `--select`-narrowed rebuild. It is safe to run
            repeatedly and from several jobs.

            Omit it when the set of dbt resources itself changed (a model
            added, renamed or deleted), since only a full run creates and
            prunes entries. A full run also refreshes display names,
            descriptions, labels, entry links and the entry hierarchy, which
            this flag leaves alone; and because a full run must write every
            entry's required aspects, run it from as complete an artifact set
            as your pipeline can produce.

            The first ingestion into an entry group must be a full run: there
            are no entries to attach aspects to yet."""),
    )
    parser.add_argument(
        '--include-entry-links',
        action='store_true',
        default=True,
        help="""Also emit EntryLink records capturing dbt lineage and semantic
        relationships (depends-on-lineage-imported, represents, depends-on-imported, etc.).""",
    )
    parser.add_argument(
        '--skip-bigquery-link',
        action='store_true',
        default=False,
        help="""Skip `represents` links (dbt node -> physical BigQuery
        table entry). Otherwise a `represents` link is emitted for each
        materialized dbt node (model/seed/snapshot) whose BigQuery dataset lives
        in the import location (`--location`); links can only reference
        @bigquery entries in that same region, so datasets in another region are
        skipped automatically. Use this flag when the BigQuery tables are not
        cataloged in Dataplex.""",
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

    # Resolve the upload destination before doing any work: downloading the
    # artifacts and transforming them is the expensive part, and a malformed
    # --storage-uri would otherwise only surface after both.
    storage_prefix = self._JobStoragePrefix(args.storage_uri, metadata_job_id)

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

    # An entry link is structure, not metadata about an entry, so it belongs to
    # the same pass that creates and prunes entries. Emitting links from an
    # aspect-only run would also put entryLink items in a job whose entry sync
    # mode cannot act on them.
    include_entry_links = args.include_entry_links and not args.aspects_only
    if args.aspects_only and args.IsSpecified('include_entry_links'):
      log.warning(
          'Ignoring --include-entry-links: --aspects-only updates aspects on '
          'existing entries and emits no entry links.'
      )

    # 1. Transform dbt artifacts into a JSONL import file in a temp dir.
    with files.TemporaryDirectory() as tmp_dir:
      # Everything below reads the artifacts off the filesystem, so a Cloud
      # Storage --artifacts-path is fetched into the temp dir first.
      artifacts_path = args.artifacts_path
      if dbt_artifacts.IsCloudStoragePath(artifacts_path):
        artifacts_path = dbt_artifacts.Download(
            artifacts_path, os.path.join(tmp_dir, 'artifacts')
        )

      # Resolve which datasets get represents (physical) links
      # (dbt node -> physical @bigquery table entry). Those links can only
      # reference @bigquery entries in the import location, so datasets in
      # another region are dropped.
      linkable_datasets = self._ResolveLinkableDatasets(
          args, artifacts_path, location, include_entry_links
      )

      local_jsonl = os.path.join(tmp_dir, _JSONL_FILENAME)
      summary = dbt_transform.GenerateImportFile(
          artifacts_path=artifacts_path,
          output_path=local_jsonl,
          eg_project=project_number,
          eg_project_id=project_id,
          eg_location=location,
          entry_group=args.entry_group,
          connector_types_project=connector_types_project,
          system_types_project=system_types_project,
          types_location=types_location,
          include_entry_links=include_entry_links,
          linkable_datasets=linkable_datasets,
      )
      log.status.Print(
          'Transformed dbt artifacts: {0} entries, {1} entry links.'.format(
              summary['entries'], summary['entry_links']
          )
      )
      if args.aspects_only:
        # An aspect-only import skips an entry that does not exist yet and
        # reports success either way, so a dbt resource added since the last
        # full run goes missing with nothing in the output to say so.
        log.status.Print(
            'Aspect-only import: aspects are written to entries that already '
            'exist; no entry is created, deleted or re-parented, and no entry '
            'link is emitted. Re-run without --aspects-only if this project '
            'has gained, renamed or dropped a resource since the last full '
            'run.'
        )
      elif not summary['entries']:
        # A full run replaces the entry group's dbt contents, so importing an
        # empty set is a request to delete all of them -- almost always a
        # mistyped --artifacts-path rather than an intent.
        raise exceptions.Error(
            'The dbt artifacts at [{0}] describe no resources, so this run '
            'would delete every dbt entry already in entry group [{1}]. Check '
            'that --artifacts-path points at the intended dbt project, or pass '
            '--aspects-only to leave the entry set alone.'.format(
                args.artifacts_path, args.entry_group
            )
        )

      # 2. Upload the JSONL under a per-job prefix (avoids stale-file
      #    duplicates) and point the import job at that prefix.
      object_uri = storage_prefix + _JSONL_FILENAME
      log.status.Print('Uploading import file to {0} ...'.format(object_uri))
      storage_api.StorageClient().CopyFileToGCS(
          local_jsonl, storage_util.ObjectReference.FromUrl(object_uri)
      )

    # 3. Build and submit the import job referencing the dbt connector types.
    entry_link_types = None
    referenced_entry_scopes = None
    extra_aspect_types = None
    if include_entry_links:
      entry_link_types = dbt_transform.LinkTypeFqns(
          system_types_project, types_location
      )
      # Scope the caller's project plus any BigQuery projects that
      # represents (physical) links target, so those cross-entry references
      # resolve.
      referenced_entry_scopes = ['projects/{0}'.format(project_number)] + [
          'projects/{0}'.format(p) for p in summary.get('bigquery_projects', [])
      ]
      # The schema-join aspect type needs a dedicated permission on the entry
      # group, so only pull it into scope when a link actually carries it.
      if summary.get('schema_join_links'):
        extra_aspect_types = dbt_transform.LinkAspectTypeFqns(
            system_types_project, types_location
        )

    job = dbt_job_lib.GenerateImportMetadataJob(
        eg_project=project_number,
        eg_location=location,
        entry_group=args.entry_group,
        connector_types_project=connector_types_project,
        system_types_project=system_types_project,
        source_storage_uri=storage_prefix,
        # The service accepts exactly two pairings: entry FULL or NONE, always
        # with aspect INCREMENTAL (ValidateMetadataJobGraph's
        # validateEntrySyncMode / validateAspectSyncMode). NONE is the
        # aspect-only import, which skips the required-aspect union the FULL
        # path applies to the write mask, so an aspect this run did not observe
        # is left as it is.
        entry_sync_mode='NONE' if args.aspects_only else 'FULL',
        aspect_sync_mode='INCREMENTAL',
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

    # Always surface the operation and the job ID.
    job_id = metadata_job_id or self._ServerGeneratedJobId(create_req_op)
    if job_id:
      log.status.Print(
          'Submitted dbt metadata import job [{0}] with operation [{1}].'
          .format(job_id, create_req_op.name)
      )
    else:
      log.status.Print(
          'Submitted dbt metadata import job with operation [{0}].'.format(
              create_req_op.name
          )
      )

    if getattr(args, 'async_', False):
      return

    # The create operation only confirms the job was accepted. Wait for it, then
    # poll the job itself until the import reaches a terminal state so we can
    # report the real outcome (and fail on a failed import).
    try:
      metadata_job_lib.WaitForOperation(create_req_op)
      if not job_id:
        # Without the id we can't address the job to poll; the create succeeded.
        log.status.Print(
            'dbt metadata import job created in [{0}].'.format(parent)
        )
        return
      result = self._WaitForImport(
          dataplex_client,
          message,
          '{0}/metadataJobs/{1}'.format(parent, job_id),
      )
    except waiter.TimeoutError as exc:
      raise exceptions.Error(self._TimedOutMessage(job_id, parent)) from exc
    self._ReportImportOutcome(job_id, result)

  def _TimedOutMessage(self, job_id: str | None, parent: str) -> str:
    """Explains that waiting stopped but the import job did not."""
    label = '[{0}] '.format(job_id) if job_id else ''
    project, location = parent.split('/')[1], parent.split('/')[3]
    if job_id:
      how_to_check = (
          'gcloud dataplex metadata-jobs describe {0} --project={1} '
          '--location={2}'.format(job_id, project, location)
      )
    else:
      how_to_check = (
          'gcloud dataplex metadata-jobs list --project={0} '
          '--location={1}'.format(project, location)
      )
    return (
        'Timed out waiting for dbt metadata import job {0}to finish. The job '
        'was submitted and is still running -- this is not an import failure. '
        'Check its outcome with:\n  {1}\nPass --async to submit without '
        'waiting.'.format(label, how_to_check)
    )

  def _ResolveLinkableDatasets(
      self,
      args: parser_extensions.Namespace,
      artifacts_path: str,
      location: str,
      include_entry_links: bool,
  ) -> frozenset[tuple[str, str]] | None:
    """Returns the BigQuery datasets to emit represents links for.

    A represents link points a dbt node at its physical @bigquery table
    entry. The link is created in the caller's entry group at the import
    location; Dataplex only supports same-region entry links, and the @bigquery
    entry of a BigQuery table lives in the Dataplex region matching its dataset.
    So a link is only valid when the dataset is in the import location -- its
    region is not a choice, it is always the import location. A live BigQuery
    lookup is used only to drop datasets that demonstrably live elsewhere;
    callers who can't do that lookup or don't want these links pass
    --skip-bigquery-link.

    Args:
      args: the parsed command arguments.
      artifacts_path: the local directory holding the dbt artifacts.
      location: the import location (the entry group / metadata job region).
      include_entry_links: whether this run emits entry links at all.

    Returns:
      The set of (project, dataset) pairs to emit links for, or None when
      represents links are disabled or nothing is co-located with the
      import location.
    """
    if not include_entry_links or args.skip_bigquery_link:
      return None
    datasets = dbt_transform.MaterializedBigQueryDatasets(artifacts_path)
    if not datasets:
      return None
    # Drop only datasets we can prove live in another region. Datasets we can't
    # read (no bigquery.datasets.get access, or not found) are kept
    # optimistically -- the import reports an unresolved @bigquery target as a
    # non-fatal per-link error.
    resolved = bq_loc.ResolveDatasetLocations(datasets)
    mismatched = {
        dataset: region
        for dataset, region in resolved.items()
        if region != location
    }
    linkable = frozenset(datasets - set(mismatched))
    if mismatched:
      log.warning(
          'Skipping represents links for {0} BigQuery dataset(s) not in '
          'the import location [{1}]: {2}. Entry links must be same-region, so '
          '@bigquery entries in another region cannot be linked; run the '
          'import in that region (--location) to link them.'.format(
              len(mismatched),
              location,
              ', '.join(
                  '{0}.{1} [{2}]'.format(project, dataset, region)
                  for (project, dataset), region in sorted(mismatched.items())
              ),
          )
      )
    return linkable or None

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
      # The entry group may well exist, so don't block the import on a
      # best-effort check that Get can be stricter about than the import job
      # is. Warn rather than swallow: when the asynchronous import then fails,
      # this is the line that explains why.
      log.warning(
          'Could not verify that entry group [{0}] exists ({1}). Continuing. '
          'If the import job fails, check that the entry group exists in '
          'project [{2}], location [{3}] and that the caller has '
          'dataplex.entryGroups.get on it.'.format(
              entry_group, _HttpErrorSummary(exc), project_id, location
          )
      )

  def _GetMetadataJobId(self, metadata_job: resources.Resource) -> str | None:
    metadata_job_id = metadata_job.RelativeName().split('/')[-1]
    if metadata_job_id == resource_args.GENERATE_ID:
      return None
    return metadata_job_id

  def _ServerGeneratedJobId(self, operation) -> str | None:
    """Returns the metadata job id the server assigned to a create operation.

    The id is only unknown locally when it wasn't passed on the command line.
    The server records it as the operation's target resource path when the
    operation is created -- available even with --async -- so it can be surfaced
    without waiting for the import to finish. Returns None if it isn't there.

    Args:
      operation: The create long-running operation.
    """
    if operation is None or operation.metadata is None:
      return None
    target = encoding.MessageToPyValue(operation.metadata).get('target')
    return target.split('/')[-1] if target else None

  def _WaitForImport(self, dataplex_client, messages, job_name):
    """Polls the metadata job until the import reaches a terminal state.

    Args:
      dataplex_client: The Dataplex API client.
      messages: The Dataplex message module.
      job_name: The full metadata job resource name to poll.

    Returns:
      The finished GoogleCloudDataplexV1MetadataJob resource.
    """
    poller = _ImportJobPoller(
        dataplex_client.projects_locations_metadataJobs, messages
    )
    return waiter.WaitFor(
        poller,
        job_name,
        'Waiting for dbt metadata import job [{0}] to finish'.format(
            job_name.split('/')[-1]
        ),
    )

  def _ReportImportOutcome(self, job_id: str | None, result) -> None:
    """Reports the finished import job's state and entry counts.

    The create operation completing doesn't mean the import succeeded: the job
    can finish SUCCEEDED, SUCCEEDED_WITH_ERRORS, FAILED or CANCELED. Surface the
    real state (and the entry counts) rather than a blanket "created", and fail
    the command on a failed or canceled import.

    Args:
      job_id: The metadata job id, if known.
      result: The finished GoogleCloudDataplexV1MetadataJob resource.

    Raises:
      exceptions.Error: If the import job failed or was canceled.
    """
    label = 'dbt metadata import job'
    if job_id:
      label = '{0} [{1}]'.format(label, job_id)
    status = getattr(result, 'status', None)
    state = (
        str(status.state) if status and status.state else 'STATE_UNSPECIFIED'
    )
    message = status.message if status and status.message else ''
    suffix = ': {0}'.format(message) if message else ''

    if state in ('FAILED', 'CANCELED'):
      raise exceptions.Error('{0} {1}{2}'.format(label, state.lower(), suffix))
    if state == 'SUCCEEDED_WITH_ERRORS':
      log.warning('{0} completed with errors{1}'.format(label, suffix))
    elif state == 'SUCCEEDED':
      log.status.Print('{0} succeeded.'.format(label))
    else:
      log.status.Print('{0} finished.'.format(label))

    counts = self._ImportCounts(getattr(result, 'importResult', None))
    if counts:
      log.status.Print('  {0}'.format(counts))

  def _ImportCounts(self, import_result) -> str:
    """Returns a compact summary of import entry / link counts, or ''."""
    if import_result is None:
      return ''
    entries = ', '.join(
        '{0} {1}'.format(n, name)
        for name, n in (
            ('created', import_result.createdEntries),
            ('updated', import_result.updatedEntries),
            ('recreated', import_result.recreatedEntries),
            ('deleted', import_result.deletedEntries),
            ('unchanged', import_result.unchangedEntries),
        )
        if n
    )
    links = ', '.join(
        '{0} {1}'.format(n, name)
        for name, n in (
            ('created', import_result.createdEntryLinks),
            ('deleted', import_result.deletedEntryLinks),
            ('unchanged', import_result.unchangedEntryLinks),
        )
        if n
    )
    parts = []
    if entries:
      parts.append('entries: {0}'.format(entries))
    if links:
      parts.append('entry links: {0}'.format(links))
    return '; '.join(parts)

  def _GetProjectNumber(self, project_id: str) -> str:
    project_ref = projects_util.ParseProject(project_id)
    return str(projects_api.Get(project_ref).projectNumber)

  def _JobStoragePrefix(
      self, storage_uri: str, metadata_job_id: str | None
  ) -> str:
    """Returns gs://bucket/<prefix>/<job-id>/ for the per-job upload.

    Args:
      storage_uri: the raw --storage-uri value.
      metadata_job_id: the metadata job id, or None when the server assigns it.

    Returns:
      The gs:// prefix the import file is uploaded under.

    Raises:
      calliope_exceptions.InvalidArgumentException: if --storage-uri is not a
        valid Cloud Storage path.
    """
    prefix = storage_uri if storage_uri.endswith('/') else storage_uri + '/'
    # ObjectReference rejects a malformed path with ValueError subclasses, which
    # gcloud would report as a crash (and file a crash report) rather than as a
    # bad flag value. Probe with the file name the caller would end up with, so
    # a bare `gs://` -- which would otherwise upload to a bucket named after the
    # job id -- is rejected too.
    try:
      storage_util.ObjectReference.FromUrl(prefix + _JSONL_FILENAME)
    except ValueError as e:
      raise calliope_exceptions.InvalidArgumentException(
          '--storage-uri',
          '[{0}] is not a valid Cloud Storage path; expected '
          'gs://BUCKET/FOLDER.'.format(storage_uri),
      ) from e
    # A server-generated job id isn't known at upload time; use a unique folder
    # so concurrent server-id jobs sharing this storage-uri don't overwrite each
    # other's import file.
    job_folder = metadata_job_id or 'dbt-import-{0}'.format(uuid.uuid4().hex)
    return '{0}{1}/'.format(prefix, job_folder)
