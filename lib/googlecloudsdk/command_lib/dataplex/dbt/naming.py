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

import collections
from collections.abc import Container, Mapping
import dataclasses
import re
from typing import Any

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

# entryLinkType ids the transform emits. The fully-qualified name is built per
# run against the resolved system-types project via ``Context.link_type_fqn``.
# An edge is typed by what it asserts. REFERENCE covers an association drawn
# from metadata (parent_map dependencies, tests to models, metrics to semantic
# models, and dbt nodes to the physical BigQuery tables they materialize to);
# SCHEMA_JOIN covers a column-level join relationship between two schemas.
REFERENCE_LINK_TYPE = 'reference'
SCHEMA_JOIN_LINK_TYPE = 'schema-join'

LINK_TYPE_IDS: tuple[str, ...] = (
    REFERENCE_LINK_TYPE,
    SCHEMA_JOIN_LINK_TYPE,
)

# dbt resource types that materialize to a physical relation, and so are what a
# `ref()` or a foreign key's `to:` can point at.
MATERIALIZED_RESOURCE_TYPES = frozenset(['model', 'seed', 'snapshot'])


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


def version_string(value: Any) -> str:
  """Renders a dbt ``version`` / ``latest_version`` value as a string.

  dbt lets a version be a number or a label, and a single model can declare
  both (``v: 1`` alongside ``v: beta``), so the two are only comparable once
  rendered.

  Args:
    value: the raw dbt version value, or None on an unversioned resource.

  Returns:
    The version as a string, or '' when the resource declares none.
  """
  return '' if value is None else str(value)


def resource_name(node: dict[str, Any]) -> str:
  """The name identifying a dbt resource within its fullyQualifiedName.

  Every version of a versioned model carries the same ``name``, so the version
  is folded into it as ``<name>_v<version>``. That is dbt's own default alias
  and warehouse relation name for the version, and it keeps the dbt FQN at the
  three segments the Dataplex FQN grammar accepts. An unversioned resource
  keeps the name it already has, so nothing already imported churns.

  A dbt version may be a decimal, and a dot here would open a fourth segment,
  which the grammar rejects. dbt writes such a version as ``_v1_5`` in the
  relation name; the FQN follows it.

  Args:
    node: the dbt resource.

  Returns:
    The resource-name segment of the FQN, or '' when the resource is unnamed.
  """
  name = node.get('name') or ''
  version = version_string(node.get('version')).replace('.', '_')
  return f'{name}_v{version}' if name and version else name


def display_name(node: dict[str, Any]) -> str:
  """The label a dbt resource is shown under.

  A versioned model is shown as ``<name>.v<version>``, dbt's own notation for
  one version of a model, so that its versions are told apart in the catalog.

  Args:
    node: the dbt resource.

  Returns:
    The display name, or '' when the resource is unnamed.
  """
  name = node.get('name') or ''
  version = version_string(node.get('version'))
  return f'{name}.v{version}' if name and version else name


def _latest_version(holders: list[tuple[str, dict[str, Any]]]) -> str | None:
  """The latest version's unique_id, when one model holds a whole name.

  Args:
    holders: the (unique_id, node) pairs sharing one resource name.

  Returns:
    The unique_id of the version a version-less ``ref()`` resolves to, or None
    when the name is held by anything other than the versions of one model.
  """
  if len({node.get('package_name') for _, node in holders}) != 1:
    return None
  latest = None
  for uid, node in holders:
    version = version_string(node.get('version'))
    if not version:
      return None
    if version != version_string(node.get('latest_version')):
      continue
    if latest is not None:
      return None
    latest = uid
  return latest


def index_by_name(
    nodes: Mapping[str, Any], resource_types: Container[str]
) -> dict[str, str]:
  """Indexes dbt nodes by name, for resolving a ``ref()`` target.

  A ``ref()`` names a resource without saying which package or version it comes
  from, so a bare name has to be resolved back to a unique_id. A name held by
  more than one resource is left out rather than resolved to an arbitrary one
  of them, with one exception: when the holders are all versions of one model,
  the name resolves to the latest version, which is what dbt itself resolves a
  version-less ``ref()`` to.

  Args:
    nodes: the manifest ``nodes`` section.
    resource_types: the dbt resource types to index.

  Returns:
    A dict of resource name -> unique_id.
  """
  holders_by_name = collections.defaultdict(list)
  for uid, node in nodes.items():
    if node.get('resource_type') not in resource_types:
      continue
    name = node.get('name')
    if name:
      holders_by_name[name].append((uid, node))
  index = {}
  for name, holders in holders_by_name.items():
    uid = holders[0][0] if len(holders) == 1 else _latest_version(holders)
    if uid:
      index[name] = uid
  return index


def index_by_name_and_version(
    nodes: Mapping[str, Any], resource_types: Container[str]
) -> dict[tuple[str, str], str]:
  """Indexes dbt nodes by (name, version), for a version-pinned ``ref()``.

  A ``ref()`` that pins a version names one model outright, so it is resolved
  against the version rather than through the name alone, which would answer
  with the latest. Unversioned resources are left out, as are pairs held by
  more than one resource.

  Args:
    nodes: the manifest ``nodes`` section.
    resource_types: the dbt resource types to index.

  Returns:
    A dict of (resource name, version) -> unique_id.
  """
  index = {}
  ambiguous = set()
  for uid, node in nodes.items():
    if node.get('resource_type') not in resource_types:
      continue
    key = (node.get('name'), version_string(node.get('version')))
    if not all(key):
      continue
    if key in index:
      ambiguous.add(key)
    else:
      index[key] = uid
  for key in ambiguous:
    del index[key]
  return index


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

# Matches the version a dbt `ref(...)` pins, spelled `v=` or `version=`, with or
# without quotes around the value.
# Examples:
#   - ref('model', v=1) -> captures: "1"
#   - ref('model', version='beta') -> captures: "beta"
_REF_VERSION = re.compile(r"""\b(?:v|version)\s*=\s*['"]?([^'",)]+)['"]?""")


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


def parse_ref_version(s: str | None) -> str | None:
  """Returns the version a dbt ``ref(...)`` expression pins, if it pins one.

  ``ref('model', v=1)`` names one version of a versioned model, and resolving
  it by name alone would answer with the latest instead.

  Args:
    s: The raw dbt ``ref(...)`` expression, or None.

  Returns:
    The pinned version as a string, or None when the expression is not a
    ``ref()`` or names no version.
  """
  if not s:
    return None
  call = _REF_CALL.search(s)
  if not call:
    return None
  version = _REF_VERSION.search(call.group(1))
  return version.group(1).strip() if version else None


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
      self, entry_type: str, project_name: str, resource: str
  ) -> str:
    """Returns the FQN for a standard dbt resource (model, seed, etc.)."""
    subtype = entry_type.removeprefix('dbt-').replace('-', '_')
    return 'dbt:{0}:{1}.{2}.{3}'.format(
        subtype, self.eg_project_id, project_name, resource
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

  def link_type_fqn(self, link_type_id: str) -> str:
    """Returns the full resource name of a core entry link type."""
    return 'projects/{0}/locations/{1}/entryLinkTypes/{2}'.format(
        self.system_project, self.types_location, link_type_id
    )
