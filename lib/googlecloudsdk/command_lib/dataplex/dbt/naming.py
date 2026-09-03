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
"""Resource-name construction for the dbt -> Dataplex transform."""

from __future__ import annotations

import dataclasses
import re

from googlecloudsdk.core import exceptions as core_exceptions


class TransformError(core_exceptions.Error):
  """Raised when dbt artifacts are missing, malformed, or over a size limit.

  Extends core.exceptions.Error so gcloud reports it as a clean `ERROR:`
  message rather than an unexpected-crash traceback. Lives here (not in
  ``transform``) so lower-level modules such as ``entry_builders`` can raise it
  without importing ``transform`` -- which imports them -- and re-exported as
  ``transform.TransformError`` for callers.
  """


# Dataplex caps the length of an entry id; see
# https://cloud.google.com/dataplex/docs/quotas#limits.
MAX_ENTRY_ID_LENGTH = 4000

# Dataplex also caps the size of the metadata an import item carries (same
# quotas page). dbt resources carry arbitrary user content -- compiled SQL,
# macro bodies, wide schemas, free-form `meta` blobs -- so a single aspect or a
# whole entry can outgrow these limits; the transform fails early rather than
# copy the file to GCS and let the import job reject the item server-side.
#
# Max JSON size of a single aspect's `data`.
MAX_ASPECT_JSON_BYTES = 120 * 1024
# The reserved 1P `schema` aspect gets a much larger budget than everything
# else (see AspectDataSizeValidator), which is what lets dbt columns survive a
# wide, deeply nested schema.
MAX_SCHEMA_ASPECT_JSON_BYTES = 2 * 1024 * 1024
# The 1P `schema` aspect is additionally capped on column count, nested fields
# included, because each column becomes an addressable entry path.
MAX_SCHEMA_COLUMNS = 10000
# Max total size of one entry (all of its aspects together).
MAX_ENTRY_BYTES = 5 * 1024 * 1024
# SQL bodies are unbounded user content, and a node can carry two copies (raw
# and compiled) in one aspect, so each is capped at a quarter of the per-aspect
# budget. Budgeted in UTF-8 bytes rather than characters because
# MAX_ASPECT_JSON_BYTES is itself measured on the encoded aspect, so a
# character budget would let non-ASCII SQL outgrow it.
MAX_CODE_BYTES = 30 * 1024

# EntrySource caps, from the Entry API reference. dbt display names and
# descriptions are free-form user content, so they are clipped to these.
MAX_DISPLAY_NAME_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 2000
MAX_LABEL_LENGTH = 128

# Short emitter key -> entryLinkType id. The fully-qualified name is built per
# run against the resolved system-types project via ``Context.link_type_fqn``.
LINK_TYPE_IDS: dict[str, str] = {
    'depends_on': 'depends-on-lineage-imported',
    'schema_join': 'schema-join',
    'materializes_to': 'represents',
    'consumed_by': 'depends-on-imported',
    'defines_semantics_for': 'represents',
    'derives_from': 'depends-on-imported',
}


def entry_id(unique_id: str) -> str:
  """Maps a dbt unique_id to a Dataplex entry id.

  dbt unique_ids look like ``model.my_project.my_model``; Dataplex entry ids
  disallow dots, so they are lowercased and dots become underscores. This is
  lossy (``a.b_c`` and ``a_b.c`` both collapse to ``a_b_c``); callers that build
  many entries should watch for collisions -- see ``entry_builders``.

  Args:
    unique_id: the dbt unique_id (e.g. ``model.my_project.my_model``).

  Returns:
    The Dataplex entry id (lowercased, with dots replaced by underscores).
  """
  return unique_id.lower().replace('.', '_')


# Matches a dbt `ref(...)` call and captures the raw arguments string inside.
# Examples:
#   - ref('model') -> captures: "'model'"
#   - ref('package', 'model') -> captures: "'package', 'model'"
#   - ref('model', version=2) -> captures: "'model', version=2"
_REF_CALL = re.compile(r'ref\(([^)]*)\)')

# Matches a dbt `source(...)` call and captures the raw arguments string inside.
# Example:
#   - source('source_name', 'table_name') ->
#     captures: "'source_name', 'table_name'"
_SOURCE_CALL = re.compile(r'source\(([^)]*)\)')

# Matches a single- or double-quoted string and captures the text inside.
# Used to extract clean string values from the arguments of ref() or source().
# Examples:
#   - "'my_model'" -> captures: "my_model"
#   - '"events"' -> captures: "events"
_QUOTED = re.compile(r"""['"]([^'"]+)['"]""")


def parse_ref(s: str | None) -> str | None:
  """Returns the target model name from a dbt ``ref(...)`` expression.

  The model name is the last quoted positional argument -- ``ref('model')``,
  ``ref('package', 'model')`` or ``ref('model', version=...)``. Positional
  arguments always come before keyword arguments, so we stop at the first
  keyword argument; this keeps a quoted keyword value like ``version='1'`` from
  being mistaken for the model name.

  Args:
    s: The raw dbt ``ref(...)`` expression, or None.

  Returns:
    The referenced model name, or None if ``s`` is empty or has no quoted
    positional argument.
  """
  if not s:
    return None
  call = _REF_CALL.search(s)
  if not call:
    return None
  model = None
  for arg in call.group(1).split(','):
    if '=' in arg:  # A keyword argument (e.g. version=1); positionals end here.
      break
    quoted = _QUOTED.search(arg)
    if quoted:
      model = quoted.group(1).strip()
  return model


def parse_source(s: str | None) -> tuple[str, str] | None:
  """Extracts the source and table name from a dbt `source(...)` expression.

  A valid dbt source call must contain exactly two quoted positional arguments:
  the source name (logical grouping/schema) and the table name.

  Example:
    - "source('raw_data', 'clicks')" -> returns ("raw_data", "clicks")

  Args:
    s: The raw dbt `source(...)` expression string.

  Returns:
    A tuple of (source_name, table_name), or None if parsing fails or is
    invalid.
  """
  if not s:
    return None
  call = _SOURCE_CALL.search(s)
  if not call:
    return None
  args = []
  for arg in call.group(1).split(','):
    quoted = _QUOTED.search(arg)
    if quoted:
      args.append(quoted.group(1).strip())
  if len(args) == 2:
    return args[0], args[1]
  return None


@dataclasses.dataclass(frozen=True)
class Context:
  """Holds the naming context for one transform run.

  Three distinct coordinates are involved (the fields cluster into a small
  struct so callers construct them by keyword and can't silently transpose two
  same-typed project strings):

  * The dbt ENTRIES live in the user's own entry group, identified by the
    project NUMBER (``eg_project``) and the entry group's regional location
    (``eg_location``). dbt entry names and entry-link names use these.
  * The dbt aspect / entry types are "connector" 1P types owned by a dedicated
    project per environment (dataplex-connector-types / dataplex-staging-3p-
    types / dataplex-autopush-3p-types) at the `global` location. entryType /
    aspectType references and the aspect map keys use this ``connector_project``
    ID (e.g. `dataplex-staging-3p-types.global.dbt-node`), not a project number.
  * The `contacts` aspect type and the entry link types are CORE 1P types owned
    by a different ``system_project`` (dataplex-types / dataplex-staging-types /
    dataplex-autopush-types), also at `global`.
  """

  eg_project: str
  eg_project_id: str
  eg_location: str
  entry_group: str
  connector_project: str
  system_project: str
  types_location: str

  def dbt_project_fqn(self, project_name: str) -> str:
    """Returns the FQN for a dbt project entry."""
    return 'dbt:project:{0}.{1}'.format(self.eg_project_id, project_name)

  def dbt_source_fqn(
      self, project_name: str, source_name: str, table_name: str
  ) -> str:
    """Returns the FQN for a dbt source entry."""
    return 'dbt:source:{0}.{1}.{2}.{3}'.format(
        self.eg_project_id, project_name, source_name, table_name
    )

  def dbt_resource_fqn(
      self, entry_type: str, project_name: str, resource_name: str
  ) -> str:
    """Returns the FQN for a standard dbt resource (model, seed, etc.)."""
    subtype = entry_type.removeprefix('dbt-').replace('-', '_')
    return 'dbt:{0}:{1}.{2}.{3}'.format(
        subtype, self.eg_project_id, project_name, resource_name
    )

  def entry_name(self, resource_entry_id: str) -> str:
    """Returns the full resource name of a dbt entry in the entry group."""
    return 'projects/{0}/locations/{1}/entryGroups/{2}/entries/{3}'.format(
        self.eg_project, self.eg_location, self.entry_group, resource_entry_id
    )

  def entry_type(self, name: str) -> str:
    """Returns the full resource name of a connector-owned entry type."""
    return 'projects/{0}/locations/{1}/entryTypes/{2}'.format(
        self.connector_project, self.types_location, name
    )

  def aspect_fqn(self, name: str) -> str:
    """Returns the full resource name of a connector-owned aspect type."""
    return 'projects/{0}/locations/{1}/aspectTypes/{2}'.format(
        self.connector_project, self.types_location, name
    )

  def aspect_key(self, name: str) -> str:
    """Returns the connector-owned aspect's key for the entry's aspect map."""
    return '{0}.{1}.{2}'.format(
        self.connector_project, self.types_location, name
    )

  def contacts_fqn(self) -> str:
    """Returns the full resource name of the core `contacts` aspect type."""
    return 'projects/{0}/locations/{1}/aspectTypes/contacts'.format(
        self.system_project, self.types_location
    )

  def contacts_key(self) -> str:
    """Returns the `contacts` aspect's key for the entry's aspect map."""
    return '{0}.{1}.contacts'.format(self.system_project, self.types_location)

  def schema_fqn(self) -> str:
    """Returns the full resource name of the core 1P `schema` aspect type."""
    return (
        f'projects/{self.system_project}/locations/{self.types_location}/'
        'aspectTypes/schema'
    )

  def schema_key(self) -> str:
    """Returns the 1P `schema` aspect's key for the entry's aspect map."""
    return f'{self.system_project}.{self.types_location}.schema'

  def schema_join_fqn(self) -> str:
    """Returns the full resource name of the core `schema-join` aspect type."""
    return (
        f'projects/{self.system_project}/locations/{self.types_location}/'
        'aspectTypes/schema-join'
    )

  def schema_join_key(self) -> str:
    """Returns the `schema-join` aspect's key for a link's aspect map."""
    return f'{self.system_project}.{self.types_location}.schema-join'

  def link_type_fqn(self, short_name: str) -> str:
    """Returns the full resource name of a core entry link type."""
    return 'projects/{0}/locations/{1}/entryLinkTypes/{2}'.format(
        self.system_project, self.types_location, LINK_TYPE_IDS[short_name]
    )
