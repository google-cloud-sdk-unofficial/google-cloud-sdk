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
"""Helpers for the dbt metadata import job command."""

from __future__ import annotations

from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.dataplex.v1 import dataplex_v1_messages

# The dbt connector types are deployed as first-party system types under an
# environment-specific project at the `global` location.
_DBT_ENTRY_TYPES = (
    'dbt-project',
    'dbt-model',
    'dbt-source',
    'dbt-seed',
    'dbt-snapshot',
    'dbt-group',
    'dbt-exposure',
    'dbt-metric',
    'dbt-macro',
    'dbt-semantic-model',
    'dbt-saved-query',
    'dbt-test',
)

_DBT_ASPECT_TYPES = (
    'dbt-node',
    'dbt-project',
    'dbt-model',
    'dbt-source',
    'dbt-seed',
    'dbt-snapshot',
    'dbt-group',
    'dbt-exposure',
    'dbt-metric',
    'dbt-macro',
    'dbt-semantic-model',
    'dbt-saved-query',
    'dbt-schema',
    'dbt-data-quality',
    'dbt-model-contracts',
)

# The dbt aspect/entry types are "connector" first-party types owned by a
# dedicated project per environment. The `contacts` aspect and the entry link
# types are core first-party types owned by a different project. Both are keyed
# by the Dataplex environment, inferred from the endpoint (or overridden by
# flags).
_CONNECTOR_TYPES_PROJECT_BY_ENV = {
    'prod': 'dataplex-connector-types',
    'staging': 'dataplex-staging-3p-types',
    'autopush': 'dataplex-autopush-3p-types',
}
_SYSTEM_TYPES_PROJECT_BY_ENV = {
    'prod': 'dataplex-types',
    'staging': 'dataplex-staging-types',
    'autopush': 'dataplex-autopush-types',
}
# The 1P dbt types always live at the `global` location.
_GLOBAL_TYPE_LOCATION = 'global'


def DetectEnvironment() -> str:
  """Infers prod/staging/autopush from the Dataplex endpoint override.

  Reads the `api_endpoint_overrides/dataplex` property (which the
  CLOUDSDK_API_ENDPOINT_OVERRIDES_DATAPLEX env var also feeds). Defaults to
  'prod' when no override (or an unrecognized one) is set.

  This is a best-effort substring match on the endpoint host; the
  `--connector-types-project` / `--system-types-project` flags exist to
  override the inferred projects when the heuristic is insufficient.

  Returns:
    One of 'prod', 'staging' or 'autopush'.
  """
  override = properties.VALUES.api_endpoint_overrides.dataplex.Get() or ''
  override = override.lower()
  if 'autopush' in override:
    return 'autopush'
  if 'staging' in override:
    return 'staging'
  return 'prod'


def ResolveConnectorTypesProject(explicit: str | None = None) -> str:
  """Project owning the dbt aspect/entry types: flag wins, else by env."""
  return explicit or _CONNECTOR_TYPES_PROJECT_BY_ENV[DetectEnvironment()]


def ResolveSystemTypesProject(explicit: str | None = None) -> str:
  """Project owning `contacts` + entry link types: flag wins, else by env."""
  return explicit or _SYSTEM_TYPES_PROJECT_BY_ENV[DetectEnvironment()]


def EntryTypeNames(connector_types_project: str) -> list[str]:
  """Relative resource names of the dbt entry types (connector project)."""
  return [
      f'projects/{connector_types_project}/locations/'
      f'{_GLOBAL_TYPE_LOCATION}/entryTypes/{n}'
      for n in _DBT_ENTRY_TYPES
  ]


def AspectTypeNames(
    connector_types_project: str,
    system_types_project: str,
) -> list[str]:
  """Relative resource names of the dbt aspect types + `contacts`.

  dbt-* aspect types come from the connector project; `contacts` is a core 1P
  type from the system project.

  Args:
    connector_types_project: project hosting the dbt aspect types.
    system_types_project: project hosting the core `contacts` aspect type.

  Returns:
    A list of aspect type resource names (dbt aspect types + `contacts`).
  """
  names = [
      f'projects/{connector_types_project}/locations/'
      f'{_GLOBAL_TYPE_LOCATION}/aspectTypes/{n}'
      for n in _DBT_ASPECT_TYPES
  ]
  names.append(
      f'projects/{system_types_project}/locations/'
      f'{_GLOBAL_TYPE_LOCATION}/aspectTypes/contacts'
  )
  return names


def EntryGroupName(project: str, location: str, entry_group: str) -> str:
  """Relative resource name of the entry group receiving dbt entries."""
  return f'projects/{project}/locations/{location}/entryGroups/{entry_group}'


def GenerateImportMetadataJob(
    eg_project: str,
    eg_location: str,
    entry_group: str,
    *,
    connector_types_project: str,
    system_types_project: str,
    source_storage_uri: str,
    entry_sync_mode: str,
    aspect_sync_mode: str,
    entry_link_types: list[str] | None = None,
    referenced_entry_scopes: list[str] | None = None,
    log_level: str | None = None,
) -> dataplex_v1_messages.GoogleCloudDataplexV1MetadataJob:
  """Builds an IMPORT MetadataJob scoped to the 1P dbt connector types.

  Args:
    eg_project: project owning the entry group receiving dbt entries.
    eg_location: region of the entry group.
    entry_group: short id of the entry group.
    connector_types_project: project hosting the dbt aspect/entry types
      (dataplex-connector-types / dataplex-staging-3p-types / ...).
    system_types_project: project hosting `contacts` + entry link types
      (dataplex-types / dataplex-staging-types / ...).
    source_storage_uri: gs:// prefix containing the import JSONL file(s).
    entry_sync_mode: 'FULL' or 'INCREMENTAL'.
    aspect_sync_mode: 'FULL' or 'INCREMENTAL'.
    entry_link_types: optional list of entryLinkType FQNs (only when emitting
      entry links).
    referenced_entry_scopes: optional list of `projects/{id}` scopes used to
      resolve entry-link / cross-project references.
    log_level: optional 'DEBUG' or 'INFO'.

  Returns:
    A GoogleCloudDataplexV1MetadataJob IMPORT message.
  """
  module = dataplex_api.GetMessageModule()
  # Alias the verbose generated message classes to keep lines within 80 cols.
  import_spec_cls = module.GoogleCloudDataplexV1MetadataJobImportJobSpec
  scope_cls = module.GoogleCloudDataplexV1MetadataJobImportJobSpecImportJobScope
  spec = import_spec_cls(
      aspectSyncMode=import_spec_cls.AspectSyncModeValueValuesEnum(
          aspect_sync_mode
      ),
      entrySyncMode=import_spec_cls.EntrySyncModeValueValuesEnum(
          entry_sync_mode
      ),
      scope=scope_cls(
          entryGroups=[EntryGroupName(eg_project, eg_location, entry_group)],
          entryTypes=EntryTypeNames(connector_types_project),
          aspectTypes=AspectTypeNames(
              connector_types_project, system_types_project
          ),
          entryLinkTypes=entry_link_types or [],
          referencedEntryScopes=referenced_entry_scopes or [],
      ),
      sourceStorageUri=source_storage_uri,
  )
  if log_level:
    spec.logLevel = import_spec_cls.LogLevelValueValuesEnum(log_level)
  job_type = module.GoogleCloudDataplexV1MetadataJob.TypeValueValuesEnum(
      'IMPORT'
  )
  return module.GoogleCloudDataplexV1MetadataJob(
      type=job_type,
      importSpec=spec,
  )
