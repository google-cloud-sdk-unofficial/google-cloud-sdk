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
``dataplex-staging-3p-types.global.dbt-node``).
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from googlecloudsdk.command_lib.dataplex.dbt import entry_builders
from googlecloudsdk.command_lib.dataplex.dbt import naming
from googlecloudsdk.core import exceptions as core_exceptions
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


class TransformError(core_exceptions.Error):
  """Raised when dbt artifacts are missing or malformed.

  Extends core.exceptions.Error so gcloud reports it as a clean `ERROR:`
  message rather than an unexpected-crash traceback.
  """


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
  if not isinstance(manifest, dict) or 'metadata' not in manifest:
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


def GenerateImportFile(  # pylint: disable=invalid-name
    artifacts_path: str,
    output_path: str,
    *,
    eg_project: str,
    eg_location: str,
    entry_group: str,
    connector_types_project: str,
    types_location: str = 'global',
) -> dict[str, Any]:
  """Transforms dbt artifacts at artifacts_path into a JSONL import file.

  Args:
    artifacts_path: directory containing dbt's target/ artifacts (manifest.json
      etc.), or a directory whose `target/` subdir contains them.
    output_path: local path the JSONL import file is written to.
    eg_project: GCP project NUMBER owning the entry group / dbt entries.
    eg_location: Dataplex region of the entry group.
    entry_group: short id of the entry group that receives the dbt entries.
    connector_types_project: project hosting the dbt aspect/entry types (e.g.
      dataplex-connector-types / dataplex-staging-3p-types); used for entryType,
      aspectType and dbt aspect keys.
    types_location: location of the system types (always `global`).

  Returns:
    A dict summary: {'entries': int, 'output': str}.

  Raises:
    TransformError: if a required artifact is missing or malformed.
  """
  # Tolerate being pointed at the project root or the target/ dir directly.
  base = artifacts_path
  if not os.path.exists(os.path.join(base, MANIFEST_FILE)):
    nested = os.path.join(base, 'target')
    if os.path.exists(os.path.join(nested, MANIFEST_FILE)):
      base = nested

  manifest = _load_json(os.path.join(base, MANIFEST_FILE), required=True)
  _warn_on_unsupported_manifest(manifest)
  catalog = _load_json(os.path.join(base, CATALOG_FILE), required=False)

  ctx = naming.Context(
      eg_project=eg_project,
      eg_location=eg_location,
      entry_group=entry_group,
      connector_project=connector_types_project,
      types_location=types_location,
  )

  entries, _ = entry_builders.build_entries(ctx, manifest, catalog)

  with files.FileWriter(output_path) as f:
    for item in entries:
      f.write(json.dumps(item) + '\n')

  return {
      'entries': len(entries),
      'output': output_path,
  }
