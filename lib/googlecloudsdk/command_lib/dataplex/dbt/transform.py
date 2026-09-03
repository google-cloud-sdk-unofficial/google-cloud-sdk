# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Transforms dbt-core artifacts into Dataplex metadata import JSONL.

This is the public entry point for the transform. It deconstructs the structured
JSON artifacts emitted by dbt-core in its ``target/`` directory (manifest.json,
catalog.json, run_results.json, sources.json) into the line-delimited JSON
(JSONL) format consumed by a Dataplex metadata import job
(``gcloud dataplex metadata-jobs create``).

It targets the first-party dbt connector types (the dbt aspect types and entry
types), which live in an environment-specific connector-types project at the
``global`` location: ``dataplex-connector-types`` (prod),
``dataplex-staging-3p-types`` (staging), or ``dataplex-autopush-3p-types``
(autopush). The dbt ENTRIES live in the caller's own entry group (their project,
a regional location); the entryType, aspectType and aspect-map keys reference
the connector-types project (the aspect key uses the connector project ID, e.g.
``dataplex-staging-3p-types.global.dbt-node``). The ``contacts`` aspect type and
the entry link types are core 1P types in a separate system project
(``dataplex-types`` / ``dataplex-staging-types`` / ``dataplex-autopush-types``).

EntryLink emission (lineage / semantic edges between entries) is implemented in
``entry_links`` and enabled by default: ``GenerateImportFile`` emits links
unless ``include_entry_links=False`` (the ``metadata-jobs create`` command
exposes this as ``--no-include-entry-links``). See ``entry_links`` and
``entry_builders`` for the per-resource and per-edge construction detail.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from googlecloudsdk.command_lib.dataplex.dbt import aspects
from googlecloudsdk.command_lib.dataplex.dbt import entry_builders
from googlecloudsdk.command_lib.dataplex.dbt import entry_links
from googlecloudsdk.command_lib.dataplex.dbt import naming
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

# dbt artifact file names, relative to the artifacts directory.
MANIFEST_FILE = 'manifest.json'
CATALOG_FILE = 'catalog.json'
RUN_RESULTS_FILE = 'run_results.json'
SOURCES_FILE = 'sources.json'

# The manifest is the only strictly required artifact -- everything else
# enriches the entries but the transform degrades gracefully without them.
REQUIRED_ARTIFACTS = (MANIFEST_FILE,)
OPTIONAL_ARTIFACTS = (CATALOG_FILE, RUN_RESULTS_FILE, SOURCES_FILE)

# dbt manifest schema versions this transform has been validated against. The
# builders read every field defensively (via .get with defaults), so an
# unlisted version still transforms -- we only warn so an unexpected manifest
# shape is easier to diagnose. See metadata.dbt_schema_version in manifest.json.
SUPPORTED_MANIFEST_SCHEMA_VERSIONS = frozenset(['v10', 'v11', 'v12'])

# Re-exported so callers importing this module reach the entry link type FQNs
# and the aspect types those links carry (both used to scope the import job)
# without importing entry_links directly.
# pylint: disable=invalid-name
LinkTypeFqns = entry_links.LinkTypeFqns
LinkAspectTypeFqns = entry_links.LinkAspectTypeFqns
# pylint: enable=invalid-name


# Re-exported so callers keep raising/catching ``transform.TransformError``.
# The class lives in ``naming`` so lower-level modules (e.g. ``entry_builders``)
# can raise it without importing this module, which imports them.
TransformError = naming.TransformError  # pylint: disable=invalid-name


def _load_json(path: str, required: bool) -> dict[str, Any]:
  """Loads a JSON artifact, returning {} when an optional file is absent.

  The manifest's shape is validated separately (see
  ``_warn_on_unsupported_manifest``); for the OPTIONAL artifacts we only need
  the top level to be a JSON object, since the builders index into them with
  ``.get()``. A valid-but-non-object optional artifact (e.g. a top-level list)
  is coerced to ``{}`` with a warning rather than crashing the builders with a
  raw ``AttributeError`` deep in the transform.

  Args:
    path: the filesystem path of the JSON artifact to load.
    required: whether the artifact must exist; a missing required artifact
      raises, while a missing optional one returns {}.

  Returns:
    The parsed JSON object, or {} when an optional artifact is absent or is not
    a JSON object.

  Raises:
    TransformError: if a required artifact is missing, or any artifact is
      present but unreadable or not valid JSON.
  """
  if not os.path.exists(path):
    if required:
      raise TransformError(
          'Required dbt artifact not found: [{0}]. Run the relevant dbt '
          'command (e.g. `dbt run`, `dbt docs generate`) first.'.format(path)
      )
    return {}
  try:
    with files.FileReader(path) as f:
      data = json.load(f)
  except (ValueError, OSError, files.Error) as e:
    # ValueError: invalid JSON; OSError/files.Error: unreadable (e.g. missing
    # read permission on the file).
    if not required:
      log.warning(
          'Optional dbt artifact [{0}] could not be read ({1}); ignoring it. '
          'Some metadata may be missing.'.format(path, e)
      )
      return {}
    raise TransformError(
        'Failed to read dbt artifact [{0}]: {1}. Ensure the file is readable '
        'and is valid dbt JSON output.'.format(path, e)
    ) from e
  if not required and not isinstance(data, dict):
    log.warning(
        'Optional dbt artifact [{0}] is not a JSON object; ignoring it.'.format(
            path
        )
    )
    return {}
  return data


def _warn_on_unsupported_manifest(manifest: dict[str, Any]) -> None:
  """Validates manifest shape and warns on an unrecognized schema version."""
  if not isinstance(manifest, dict) or manifest.get('metadata') is None:
    raise TransformError(
        'The file does not look like a dbt manifest (expected a JSON object '
        'with a "metadata" field). Point --artifacts-path at a dbt project '
        'or its target/ directory.'
    )
  schema_url = manifest.get('metadata', {}).get('dbt_schema_version') or ''
  # e.g. https://schemas.getdbt.com/dbt/manifest/v12.json -> v12
  match = re.search(r'/(v\d+)\.json', schema_url)
  version = match.group(1) if match else None
  if version and version not in SUPPORTED_MANIFEST_SCHEMA_VERSIONS:
    log.warning(
        'dbt manifest schema [{0}] has not been validated with this command '
        '(supported: {1}). The import will proceed, but some metadata may be '
        'missing or misinterpreted.'.format(
            version, ', '.join(sorted(SUPPORTED_MANIFEST_SCHEMA_VERSIONS))
        )
    )


def _artifacts_base(artifacts_path: str) -> str:
  """Returns the dir holding the dbt artifacts.

  Tolerates being pointed at the project root or the ``target/`` dir directly:
  if manifest.json is not at ``artifacts_path`` but in its ``target/`` subdir,
  returns that subdir.

  Args:
    artifacts_path: the --artifacts-path value.

  Returns:
    The directory to read manifest.json / run_results.json etc. from.
  """
  if not os.path.exists(os.path.join(artifacts_path, MANIFEST_FILE)):
    nested = os.path.join(artifacts_path, 'target')
    if os.path.exists(os.path.join(nested, MANIFEST_FILE)):
      return nested
  return artifacts_path


def MaterializedBigQueryDatasets(  # pylint: disable=invalid-name
    artifacts_path: str,
) -> set[tuple[str, str]]:
  """Returns the ``(database, schema)`` pairs the dbt run materializes into.

  Args:
    artifacts_path: the --artifacts-path value (project root or target/ dir).

  Returns:
    The set of distinct ``(database, schema)`` pairs of materialized nodes.

  Raises:
    TransformError: if manifest.json is missing or malformed.
  """
  base = _artifacts_base(artifacts_path)
  manifest = _load_json(os.path.join(base, MANIFEST_FILE), required=True)
  return entry_links.materialized_bigquery_datasets(manifest)


def _count_untyped(fields: list[dict[str, Any]]) -> tuple[int, int]:
  """Counts (untyped, total) columns in a 1P schema aspect's field tree."""
  untyped = total = 0
  for field in fields:
    total += 1
    if field.get('dataType') == aspects.UNKNOWN_DATA_TYPE:
      untyped += 1
    nested_untyped, nested_total = _count_untyped(field.get('fields') or [])
    untyped += nested_untyped
    total += nested_total
  return untyped, total


def _warn_on_untyped_columns(
    ctx: naming.Context, entries: list[dict[str, Any]]
) -> None:
  """Warns when dbt supplied no data type for some columns.

  Column types reach the artifacts only through catalog.json, which only
  `dbt docs generate` writes, and only for relations that already exist in the
  warehouse. A project that was never built -- or whose docs were generated
  before it was built -- therefore yields typeless columns. dbt itself logs
  nothing in that case, so this is the only signal the user gets.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    entries: the entry records built from the artifacts.
  """
  schema_key = ctx.schema_key()
  untyped = total = resources = 0
  for record in entries:
    aspect = (record['entry'].get('aspects') or {}).get(schema_key)
    if not aspect:
      continue
    entry_untyped, entry_total = _count_untyped(
        aspect.get('data', {}).get('fields') or []
    )
    if entry_untyped:
      resources += 1
    untyped += entry_untyped
    total += entry_total
  if not untyped:
    return
  log.warning(
      '{0} of {1} columns across {2} dbt resource(s) have no data type and are '
      'recorded as [{3}]. Column types come from catalog.json, which only '
      '`dbt docs generate` writes, and only for models that already exist in '
      'the warehouse. Run `dbt build && dbt docs generate` (same profile and '
      'target, and without --select, --no-compile or --empty-catalog), then '
      're-run this command. Ephemeral models never materialize, so their '
      'columns can only be typed by declaring data_type in schema.yml.'.format(
          untyped, total, resources, aspects.UNKNOWN_DATA_TYPE
      )
  )


def GenerateImportFile(  # pylint: disable=invalid-name
    artifacts_path: str,
    output_path: str,
    *,
    eg_project: str,
    eg_project_id: str,
    eg_location: str,
    entry_group: str,
    connector_types_project: str,
    system_types_project: str,
    types_location: str = 'global',
    include_entry_links: bool = True,
    linkable_datasets: set[tuple[str, str]] | None = None,
) -> dict[str, Any]:
  """Transforms dbt artifacts at artifacts_path into a JSONL import file.

  Args:
    artifacts_path: directory containing dbt's target/ artifacts (manifest.json
      etc.), or a directory whose `target/` subdir contains them.
    output_path: local path the JSONL import file is written to.
    eg_project: GCP project NUMBER owning the entry group / dbt entries.
    eg_project_id: GCP project ID owning the entry group / dbt entries.
    eg_location: Dataplex region of the entry group.
    entry_group: short id of the entry group that receives the dbt entries.
    connector_types_project: project hosting the dbt aspect/entry types (e.g.
      dataplex-connector-types / dataplex-staging-3p-types); used for entryType,
      aspectType and dbt aspect keys.
    system_types_project: project hosting `contacts` + entry link types (e.g.
      dataplex-types / dataplex-staging-types).
    types_location: location of the system types (always `global`).
    include_entry_links: when True (the default), also emit EntryLink records.
    linkable_datasets: the BigQuery (database, schema) datasets to emit
      materializes-to links for (dbt node -> physical @bigquery table entry) --
      the datasets known to live in the import location, since entry links are
      same-region and the @bigquery entries are named there. When None (or with
      include_entry_links=False), no materializes-to links are emitted.

  Returns:
    A dict summary: {'entries': int, 'entry_links': int,
    'schema_join_links': int, 'output': str, 'bigquery_projects': list[str]}.
    bigquery_projects are the BigQuery projects materializes-to links reference
    (for the import job scope); empty unless linkable_datasets was given.
    schema_join_links lets the caller keep the separately-permissioned
    schema-join aspect type out of scope when no link carries it.

  Raises:
    TransformError: if a required artifact is missing or malformed, or if an
      entry or aspect exceeds the Dataplex size limits (fails before writing the
      import file, so nothing is uploaded to GCS or handed to an import job).
  """
  base = _artifacts_base(artifacts_path)
  manifest = _load_json(os.path.join(base, MANIFEST_FILE), required=True)
  _warn_on_unsupported_manifest(manifest)
  catalog = _load_json(os.path.join(base, CATALOG_FILE), required=False)
  run_results = _load_json(os.path.join(base, RUN_RESULTS_FILE), required=False)
  sources = _load_json(os.path.join(base, SOURCES_FILE), required=False)

  ctx = naming.Context(
      eg_project=eg_project,
      eg_project_id=eg_project_id,
      eg_location=eg_location,
      entry_group=entry_group,
      connector_project=connector_types_project,
      system_project=system_types_project,
      types_location=types_location,
  )

  entries, known_ids = entry_builders.build_entries(
      ctx, manifest, catalog, run_results, sources
  )
  _warn_on_untyped_columns(ctx, entries)
  links = []
  if include_entry_links:
    links = entry_links.build_entry_links(
        ctx, manifest, known_ids, linkable_datasets=linkable_datasets
    )
  # Scope only the projects whose datasets are actually linked.
  bigquery_projects = []
  if include_entry_links and linkable_datasets:
    bigquery_projects = sorted({project for project, _ in linkable_datasets})

  with files.FileWriter(output_path, newline='\n') as f:
    for item in entries:
      f.write(json.dumps(item) + '\n')
    for item in links:
      f.write(json.dumps(item) + '\n')

  return {
      'entries': len(entries),
      'entry_links': len(links),
      'schema_join_links': sum(
          1
          for item in links
          if (item.get('entryLink') or {})
          .get('entryLinkType', '')
          .endswith('/schema-join')
      ),
      'output': output_path,
      'bigquery_projects': bigquery_projects,
  }
