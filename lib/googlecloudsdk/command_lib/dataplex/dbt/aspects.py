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
"""Shared aspect-record builders for the dbt -> Dataplex transform."""

from __future__ import annotations

from collections.abc import Callable
import json
import re
from typing import Any

from googlecloudsdk.command_lib.dataplex.dbt import naming


def make_aspect(aspect_fqn: str, data: dict[str, Any]) -> dict[str, Any]:
  """Wraps aspect data in the {aspectType, data} record shape.

  Args:
    aspect_fqn: the fully-qualified aspect type resource name.
    data: the aspect's data payload.

  Returns:
    An aspect record.
  """
  return {'aspectType': aspect_fqn, 'data': data}


def node_aspect(
    ctx: naming.Context,
    unique_id: str,
    node: dict[str, Any],
    resource_type: str,
    *,
    database: str | None = None,
    namespace: str | None = None,
) -> dict[str, Any]:
  """Builds the universal dbt-node aspect shared by every dbt entry.

  Common fields (name, filePath, packageName) are read straight from ``node``.
  ``database`` / ``namespace`` default to ``node['database']`` /
  ``node['schema']`` but can be overridden for resources that carry them
  elsewhere (e.g. a semantic model reads them from its ``node_relation``).

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    unique_id: the dbt unique_id, stored as the aspect's ``id`` field.
    node: the dbt resource dict to read name / filePath / packageName from.
    resource_type: the dbt resource type (e.g. 'model', 'source').
    database: overrides ``node['database']`` when not None.
    namespace: overrides ``node['schema']`` when not None.

  Returns:
    A dbt-node aspect record.
  """
  data = {'id': unique_id}
  name = node.get('name')
  if name:
    data['name'] = name
  database = node.get('database') if database is None else database
  if database:
    data['database'] = database
  namespace = node.get('schema') if namespace is None else namespace
  if namespace:
    data['namespace'] = namespace
  file_path = node.get('original_file_path')
  if file_path:
    data['filePath'] = file_path
  package_name = node.get('package_name')
  if package_name:
    data['packageName'] = package_name
  if resource_type:
    data['resourceType'] = resource_type
  return make_aspect(ctx.aspect_fqn('dbt-node'), data)


def base_aspects(
    ctx: naming.Context,
    unique_id: str,
    node: dict[str, Any],
    resource_type: str,
    primary_name: str,
    primary_data: dict[str, Any],
) -> dict[str, Any]:
  """The dbt-node aspect plus a resource's primary aspect, keyed for the map.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    unique_id: the dbt unique_id, stored as the node aspect's ``id`` field.
    node: the dbt resource dict passed to ``node_aspect``.
    resource_type: the dbt resource type (e.g. 'seed', 'snapshot').
    primary_name: the resource-specific aspect name (e.g. 'dbt-seed').
    primary_data: the resource-specific aspect data.

  Returns:
    An aspect map holding the dbt-node and primary aspects.
  """
  return {
      ctx.aspect_key('dbt-node'): node_aspect(
          ctx, unique_id, node, resource_type
      ),
      ctx.aspect_key(primary_name): make_aspect(
          ctx.aspect_fqn(primary_name), primary_data
      ),
  }


def contacts_aspect(
    ctx: naming.Context, identities: list[dict[str, str]]
) -> dict[str, Any]:
  """Builds the core `contacts` aspect from a list of identities.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    identities: the contact identities (see ``owner_identities``).

  Returns:
    A contacts aspect record.
  """
  return make_aspect(ctx.contacts_fqn(), {'identities': identities})


def owner_identities(owner: dict[str, Any] | None) -> list[dict[str, str]]:
  """Builds the contacts ``identities`` list from a dbt ``owner`` block.

  dbt records an owner as ``{'email': ..., 'name': ...}`` (either field may be
  absent). Per the dbt-core schema ``owner.email`` may be a single string or a
  list of strings, so a list yields one ``owner`` identity per email. We prefer
  the email(s), falling back to the name. Shared by the group and exposure
  builders.

  Args:
    owner: the dbt resource's ``owner`` mapping (or None).

  Returns:
    One ``owner`` identity per email (or a single one for the name when no email
    is set), or [] when neither field is present.
  """
  owner = owner or {}
  email = owner.get('email')
  emails = email if isinstance(email, (list, tuple)) else [email]
  names = [str(e) for e in emails if e]
  if not names and owner.get('name'):
    names = [str(owner['name'])]
  return [{'name': name, 'role': 'owner'} for name in names]


def stat_int(stats: dict[str, Any], key: str) -> int | None:
  """Returns a catalog stat as int, or None if absent / not included.

  dbt reports stat values as strings and sometimes as decimals (e.g. "2048.0"),
  so parse via float before truncating to int.

  Args:
    stats: the catalog node's ``stats`` mapping.
    key: the stat name to read (e.g. 'num_rows', 'num_bytes').

  Returns:
    The stat value as int, or None when the stat is absent or not included.
  """
  stat = stats.get(key, {})
  if not stat.get('include'):
    return None
  try:
    return int(float(stat.get('value')))
  except (TypeError, ValueError):
    return None


def add_stat(
    data: dict[str, Any], out_key: str, stats: dict[str, Any], stat_key: str
) -> None:
  """Copies a catalog stat into ``data[out_key]``, omitting it when absent."""
  value = stat_int(stats, stat_key)
  if value is not None:
    data[out_key] = value


def merged_columns(
    catalog_columns: dict[str, Any] | None,
    manifest_columns: dict[str, Any] | None,
) -> list[dict[str, Any]]:
  """Merges the catalog and manifest column metadata into one column list.

  Neither artifact is complete on its own: catalog.json carries the resolved
  warehouse data type, while the manifest carries the user's column
  ``description``. Columns are matched case-insensitively and a column present
  in only one of the two artifacts still lands. The catalog wins on data type
  because it reports what the warehouse actually built; the manifest wins on
  description because that is what the user wrote, and the catalog's
  ``comment`` may be a stale copy of an older one.

  Args:
    catalog_columns: the catalog node/source ``columns`` mapping, or None.
    manifest_columns: the manifest node/source ``columns`` mapping, or None.

  Returns:
    The merged columns, each with columnId / name / dataType / description.
  """
  fields: dict[str, dict[str, Any]] = {}

  def merge(
      columns: dict[str, Any] | None,
      type_key: str,
      desc_key: str,
      description_wins: bool = False,
  ) -> None:
    for col_name, col_data in (columns or {}).items():
      col_data = col_data or {}
      field = fields.setdefault(
          col_name.lower(),
          {
              'columnId': col_name,
              'name': col_data.get('name') or col_name,
              'dataType': '',
              'description': '',
              # Only the manifest carries these; they feed the 1P aspect.
              'constraints': [],
              'meta': {},
              'tags': [],
          },
      )
      field['dataType'] = field['dataType'] or col_data.get(type_key) or ''
      if description_wins:
        field['description'] = col_data.get(desc_key) or field['description']
      else:
        field['description'] = (
            field['description'] or col_data.get(desc_key) or ''
        )
      field['constraints'] = (
          field['constraints'] or col_data.get('constraints') or []
      )
      field['meta'] = field['meta'] or col_data.get('meta') or {}
      field['tags'] = field['tags'] or col_data.get('tags') or []

  merge(catalog_columns, 'type', 'comment')
  merge(manifest_columns, 'data_type', 'description', description_wins=True)
  return list(fields.values())


# BigQuery data type -> the 1P schema aspect's `metadataType` enum. dbt reports
# whatever string the warehouse uses, while the 1P aspect requires one of a
# fixed set; BigQuery is the only officially supported adapter, so only its
# types are mapped. The map does not have to be exhaustive on the BigQuery
# side -- an unmapped warehouse type falls back to OTHER, so a new BigQuery
# type degrades to a usable value rather than one the aspect type would reject
# -- but every value here must exist in the `schema` aspect type's metadata
# type enum, which is what the aspect type will accept.
_METADATA_TYPES = {
    'BOOL': 'BOOLEAN',
    'BOOLEAN': 'BOOLEAN',
    'INT64': 'NUMBER',
    'INT': 'NUMBER',
    'INTEGER': 'NUMBER',
    'SMALLINT': 'NUMBER',
    'BIGINT': 'NUMBER',
    'TINYINT': 'NUMBER',
    'BYTEINT': 'NUMBER',
    'NUMERIC': 'NUMBER',
    'DECIMAL': 'NUMBER',
    'BIGNUMERIC': 'NUMBER',
    'BIGDECIMAL': 'NUMBER',
    'FLOAT64': 'NUMBER',
    'FLOAT': 'NUMBER',
    'STRING': 'STRING',
    'BYTES': 'BYTES',
    'DATE': 'DATETIME',
    'DATETIME': 'DATETIME',
    'TIME': 'DATETIME',
    'TIMESTAMP': 'TIMESTAMP',
    'GEOGRAPHY': 'GEOSPATIAL',
    'STRUCT': 'STRUCT',
    'RECORD': 'STRUCT',
    # TODO: b/545043720 - Change the "RANGE" mapping back to "RANGE" once it is
    # available in the production schema aspect, which currently lacks RANGE
    # support. Temporarily mapping it to OTHER and suppressing rangeElementType
    # to bypass this blocker.
    'RANGE': 'OTHER',
}

# The 1P schema aspect requires a dataType on every field, but dbt often has no
# type at all -- a compile-only run produces no catalog, and ephemeral models
# never materialize -- so those columns are labelled rather than dropped.
UNKNOWN_DATA_TYPE = 'UNKNOWN'

# dbt's BigQuery catalog macro substitutes this literal when the warehouse
# reports no type (external table columns are absent from COLUMN_FIELD_PATHS).
_UNKNOWN_CATALOG_TYPE = '<unknown>'


def _clean_data_type(data_type: str) -> str:
  """dbt's `<unknown>` placeholder is an absent type, not a type name."""
  text = (data_type or '').strip()
  return '' if text == _UNKNOWN_CATALOG_TYPE else text


def metadata_type(data_type: str) -> str:
  """Maps a dbt data type onto the 1P schema aspect's metadataType enum.

  Args:
    data_type: the raw dbt/warehouse type string (may be empty).

  Returns:
    One of the metadataType enum values; OTHER when absent or unrecognized.
  """
  text = (data_type or '').strip().upper()
  # ARRAY<T> describes cardinality, not type: classify by the element type.
  while text.startswith('ARRAY<') and text.endswith('>'):
    text = text[len('ARRAY<') : -1].strip()
  # Drop parameters and element types: STRING(10), STRUCT<a INT64>, RANGE<DATE>.
  base = re.split(r'[<(]', text, maxsplit=1)[0].strip()
  return _METADATA_TYPES.get(base, 'OTHER')


def _has_constraint(column: dict[str, Any], constraint_type: str) -> bool:
  """Whether the dbt column declares the given constraint."""
  return any(
      ((c or {}).get('type') or '').lower() == constraint_type
      for c in column.get('constraints') or []
  )


def _field_mode(
    data_type: str, column: dict[str, Any], contract_enforced: bool | None
) -> str:
  """The 1P `mode` for a column, or '' when dbt cannot tell us.

  dbt's artifacts carry no nullability, so NULLABLE is never inferable -- only
  an ARRAY (always repeated) and an enforced not_null constraint are certain.

  Args:
    data_type: the column's dbt/warehouse type string.
    column: the merged column, read for its dbt constraints.
    contract_enforced: the node's contract ``enforced`` flag, or None when the
      node declares no contract.

  Returns:
    'REPEATED', 'REQUIRED', or '' when neither is certain.
  """
  if (data_type or '').strip().upper().startswith('ARRAY<'):
    return 'REPEATED'
  if contract_enforced and _has_constraint(column, 'not_null'):
    return 'REQUIRED'
  return ''


def _range_element_type(data_type: str) -> str:
  """The element type of a RANGE column, e.g. RANGE<DATE> -> DATE."""
  text = (data_type or '').strip().upper()
  if text.startswith('RANGE<') and text.endswith('>'):
    return text[len('RANGE<') : -1].strip()
  return ''


def _field_annotations(column: dict[str, Any]) -> dict[str, str]:
  """The 1P `annotations` map, from dbt's per-column `meta` and `tags`.

  This is the only place dbt's column-level meta and tags survive; neither has
  a dedicated field in either schema aspect. Values must be strings, so
  non-string meta values are JSON-encoded.

  Args:
    column: the merged column, read for its dbt `meta` and `tags`.

  Returns:
    The annotations map, empty when the column declares neither.
  """
  annotations = {}
  for key, value in (column.get('meta') or {}).items():
    annotations[str(key)] = (
        value if isinstance(value, str) else json.dumps(value, default=str)
    )
  tags = column.get('tags') or []
  if tags:
    annotations['tags'] = ', '.join(str(tag) for tag in tags)
  return annotations


def _contract_enforced(node: dict[str, Any]) -> bool | None:
  """Whether the node's contract is enforced, or None when it says nothing.

  dbt only renders a constraint into the warehouse DDL when the model's
  contract is enforced, so this is what decides whether every constraint the
  node declares is `enforced` in the 1P sense.

  Args:
    node: the dbt model/seed/snapshot node.

  Returns:
    The contract's ``enforced`` flag, or None when the node declares no
    contract.
  """
  enforced = (node.get('contract') or {}).get('enforced')
  return None if enforced is None else bool(enforced)


def _constraints_of(node: dict[str, Any], constraint_type: str) -> list[Any]:
  """The node's constraints of one dbt type, model- and column-level alike."""
  return [
      c
      for c in _node_and_column_constraints(node)
      if (c.get('type') or '').lower() == constraint_type
  ]


def primary_key(node: dict[str, Any]) -> dict[str, Any] | None:
  """The 1P `primaryKey` record, from dbt's model or column constraints.

  Args:
    node: the dbt model/seed/snapshot node.

  Returns:
    A primaryKey record, or None when the node declares no primary key.
  """
  columns = []
  for constraint in node.get('constraints') or []:
    if ((constraint or {}).get('type') or '').lower() == 'primary_key':
      columns = [str(c) for c in constraint.get('columns') or [] if c]
      break
  if not columns:
    # dbt also allows the constraint to sit on the column itself.
    columns = [
        col.get('name') or col_name
        for col_name, col in (node.get('columns') or {}).items()
        if _has_constraint(col or {}, 'primary_key')
    ]
  if not columns:
    return None
  key = {'fields': columns}
  enforced = _contract_enforced(node)
  if enforced is not None:
    key['enforced'] = enforced
  return key


def unique_constraints(node: dict[str, Any]) -> list[dict[str, Any]]:
  """The 1P `uniqueConstraints` records, from dbt's unique constraints.

  Only declared ``unique`` constraints are read, not the ``unique`` generic
  test: the test is already emitted as a dbt-data-quality entry, and a model
  commonly both declares the constraint and tests it.

  Args:
    node: the dbt model/seed/snapshot node.

  Returns:
    The uniqueConstraints records, empty when the node declares none.
  """
  enforced = _contract_enforced(node)
  out = []
  for constraint in _constraints_of(node, 'unique'):
    columns = [str(c) for c in constraint.get('columns') or [] if c]
    if not columns:
      # `fields` is required by the aspect type.
      continue
    record = {'fields': columns}
    if constraint.get('name'):
      record['name'] = str(constraint['name'])
    if enforced is not None:
      record['enforced'] = enforced
    out.append(record)
  return out


def check_constraints(node: dict[str, Any]) -> list[dict[str, Any]]:
  """The 1P `checkConstraints` records, from dbt's check constraints.

  Args:
    node: the dbt model/seed/snapshot node.

  Returns:
    The checkConstraints records, empty when the node declares none.
  """
  enforced = _contract_enforced(node)
  out = []
  for constraint in _constraints_of(node, 'check'):
    condition = str(constraint.get('expression') or '').strip()
    if not condition:
      # `condition` is required by the aspect type.
      continue
    record = {'condition': _redact_literals(condition)}
    if constraint.get('name'):
      record['name'] = str(constraint['name'])
    if enforced is not None:
      record['enforced'] = enforced
    out.append(record)
  return out


def foreign_keys(
    node: dict[str, Any],
    resolve_target: Callable[[str], str | None] | None,
) -> list[dict[str, Any]]:
  """The 1P `foreignKeys` records, from dbt's foreign_key constraints.

  Only explicit ``foreign_key`` constraints are read. A dbt ``relationships``
  test asserts the same thing and is already emitted as a schema-join
  entry link; reading both would double-report the common case where a model
  declares the constraint and tests it.

  ``referencedTable`` and ``fieldMappings`` are both required by the aspect
  type, so a constraint is skipped unless its ``to`` resolves to an entry and
  its local and referenced columns pair up.

  Args:
    node: the dbt model/seed/snapshot node.
    resolve_target: maps a constraint's raw ``to`` to a Dataplex entry name, or
      None when the caller cannot resolve targets (nothing is emitted then).

  Returns:
    The foreignKeys records, empty when the node declares none that resolve.
  """
  if not resolve_target:
    return []
  enforced = _contract_enforced(node)
  out = []
  for constraint in _constraints_of(node, 'foreign_key'):
    referenced = resolve_target(constraint.get('to') or '')
    if not referenced:
      continue
    # A column-level constraint carries no `columns`; it is the column it sits
    # on, which _node_and_column_constraints has already filled in.
    local = [str(c) for c in constraint.get('columns') or [] if c]
    remote = [str(c) for c in constraint.get('to_columns') or [] if c]
    if not local or len(local) != len(remote):
      # dbt allows `to_columns` to be omitted, but the 1P aspect cannot express
      # a foreign key without naming the referenced columns.
      continue
    key = {
        'referencedTable': referenced,
        'fieldMappings': [
            {'field': f, 'referencedField': r} for f, r in zip(local, remote)
        ],
    }
    if constraint.get('name'):
      key['name'] = str(constraint['name'])
    if enforced is not None:
      key['enforced'] = enforced
    out.append(key)
  return out


def _node_and_column_constraints(
    node: dict[str, Any],
) -> list[dict[str, Any]]:
  """The node's constraints, model-level first then column-level.

  Column-level constraints name no columns of their own, so each is given the
  column it was declared on -- letting callers treat both levels uniformly.

  Args:
    node: the dbt model/seed/snapshot node.

  Returns:
    The constraint dicts, each guaranteed to carry a ``columns`` list.
  """
  out = [dict(c) for c in node.get('constraints') or [] if c]
  for col_name, col in (node.get('columns') or {}).items():
    name = (col or {}).get('name') or col_name
    for constraint in (col or {}).get('constraints') or []:
      if constraint:
        out.append({**constraint, 'columns': [name]})
  return out


def _schema_field(
    column: dict[str, Any], name: str, contract_enforced: bool | None
) -> dict[str, Any]:
  """Builds one 1P schema field from a merged column."""
  data_type = _clean_data_type(column.get('dataType'))
  field = {
      'name': name,
      'dataType': data_type or UNKNOWN_DATA_TYPE,
      'metadataType': metadata_type(data_type),
  }
  if column.get('description'):
    field['description'] = column['description']
  mode = _field_mode(data_type, column, contract_enforced)
  if mode:
    field['mode'] = mode
  range_element = _range_element_type(data_type)
  if range_element and field['metadataType'] == 'RANGE':
    field['rangeElementType'] = range_element
  annotations = _field_annotations(column)
  if annotations:
    field['annotations'] = annotations
  return field


def _nested_fields(
    columns: list[dict[str, Any]], contract_enforced: bool | None
) -> list[dict[str, Any]]:
  """Rebuilds the nested field tree from BigQuery's dotted column paths.

  dbt's BigQuery catalog is built from INFORMATION_SCHEMA.COLUMN_FIELD_PATHS,
  which flattens a record column into one row per leaf keyed by its dotted path
  (``payload``, ``payload.id``, ``payload.tags``). The 1P schema aspect models
  that natively via ``fields[].fields[]``, so the paths are folded back into a
  tree and each field is named by its own last path segment.

  Args:
    columns: the merged columns from ``merged_columns``, in catalog order.
    contract_enforced: the node's contract ``enforced`` flag, threaded down to
      ``_field_mode``.

  Returns:
    The top-level fields, each with nested ``fields`` where applicable.
  """
  roots: list[dict[str, Any]] = []
  by_path: dict[tuple[str, ...], dict[str, Any]] = {}
  for column in columns:
    path = (column.get('columnId') or column.get('name') or '').split('.')
    path = [part for part in path if part]
    if not path:
      # Nothing addressable to hang a field off, and ``name`` is required.
      continue
    siblings = roots
    # Paths are keyed case-insensitively to match ``merged_columns``; without
    # that a catalog-only `Payload` and a manifest-only `payload.id` would build
    # two separate roots.
    for depth in range(1, len(path)):
      key = tuple(part.lower() for part in path[:depth])
      parent = by_path.get(key)
      if parent is None:
        # A record whose own row hasn't been seen yet (or at all): stand it up
        # so the leaf still lands in the right place.
        parent = {
            'name': path[depth - 1],
            'dataType': UNKNOWN_DATA_TYPE,
            'metadataType': 'STRUCT',
        }
        by_path[key] = parent
        siblings.append(parent)
      siblings = parent.setdefault('fields', [])
    key = tuple(part.lower() for part in path)
    field = _schema_field(column, path[-1], contract_enforced)
    placeholder = by_path.get(key)
    if placeholder is None:
      by_path[key] = field
      siblings.append(field)
    else:
      # Stood up as an ancestor earlier; fill in its real metadata in place,
      # keeping the children already attached to it.
      placeholder.update(field)
  return roots


# A check constraint's expression can embed the very values the column holds
# (`email != 'ceo@corp.com'`), and the aspect type specifies `condition` with
# literals redacted. Quoted strings and bare numbers are the two literal forms
# BigQuery check expressions use.
_STRING_LITERAL = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"")
_NUMBER_LITERAL = re.compile(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])')
_REDACTED = '<REDACTED>'


def _redact_literals(condition: str) -> str:
  """Replaces string and numeric literals in a SQL condition with a marker."""
  return _NUMBER_LITERAL.sub(
      _REDACTED, _STRING_LITERAL.sub(_REDACTED, condition)
  )


def count_fields(fields: list[dict[str, Any]]) -> int:
  """The number of fields in a 1P schema field tree, nested ones included."""
  return sum(1 + count_fields(f.get('fields') or []) for f in fields)


def _take_fields(
    fields: list[dict[str, Any]], budget: list[int]
) -> list[dict[str, Any]]:
  """Copies ``fields`` pre-order until ``budget`` runs out."""
  kept = []
  for field in fields:
    if budget[0] <= 0:
      break
    budget[0] -= 1
    taken = dict(field)
    if taken.get('fields'):
      children = _take_fields(taken['fields'], budget)
      if children:
        taken['fields'] = children
      else:
        taken.pop('fields')
    kept.append(taken)
  return kept


def fit_fields(
    fields: list[dict[str, Any]], max_columns: int, max_bytes: int
) -> list[dict[str, Any]]:
  """Drops fields until the tree fits both the column and the byte budget.

  Fields are kept pre-order, so a retained field always has its parent, and the
  result is deterministic for a given input.

  Args:
    fields: the 1P schema ``fields`` tree.
    max_columns: the most fields the tree may hold, nested ones included.
    max_bytes: the most UTF-8 bytes the serialized tree may take.

  Returns:
    The tree unchanged when it already fits, else the largest fitting prefix.
  """
  count = count_fields(fields)
  kept = fields
  if count > max_columns:
    count = max_columns
    kept = _take_fields(fields, [count])
  while kept:
    size = len(json.dumps(kept).encode('utf-8'))
    if size <= max_bytes:
      break
    count = max(0, min(count - 1, count * max_bytes // size))
    kept = _take_fields(fields, [count])
  return kept


def system_schema_aspect(
    ctx: naming.Context,
    columns: list[dict[str, Any]],
    node: dict[str, Any] | None = None,
    resolve_target: Callable[[str], str | None] | None = None,
) -> dict[str, Any] | None:
  """Builds the core 1P `schema` aspect from the same merged columns.

  This is the only schema dbt entries carry. It reconstructs real nesting
  from BigQuery's flattened dotted paths and fills the fields the catalog UI
  and search read (metadataType, mode, rangeElementType, annotations) plus
  every constraint dbt declares.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    columns: the merged columns from ``merged_columns``.
    node: the dbt node, read for its constraints.
    resolve_target: maps a foreign key's raw ``to`` to a Dataplex entry name;
      when absent, no foreign keys are emitted.

  Returns:
    A `schema` aspect record, or None when there are no columns.
  """
  if not columns:
    return None
  node = node or {}
  data = {'fields': _nested_fields(columns, _contract_enforced(node))}
  key = primary_key(node)
  if key:
    data['primaryKey'] = key
  for field, records in (
      ('foreignKeys', foreign_keys(node, resolve_target)),
      ('uniqueConstraints', unique_constraints(node)),
      ('checkConstraints', check_constraints(node)),
  ):
    if records:
      data[field] = records
  return make_aspect(ctx.schema_fqn(), data)


def model_contracts_aspect(
    ctx: naming.Context, node: dict[str, Any], enforced: bool
) -> dict[str, Any] | None:
  """Optional dbt-model-contracts aspect (only when a contract is enforced)."""
  if not enforced:
    return None
  model_constraints = [
      {
          'type': c.get('type') or '',
          'name': c.get('name') or '',
          'columns': c.get('columns') or [],
      }
      for c in node.get('constraints') or []
  ]
  column_contracts = []
  for col_name, col in (node.get('columns') or {}).items():
    col = col or {}
    column_contracts.append({
        'name': col.get('name') or col_name,
        'dataType': col.get('data_type') or '',
        'constraints': [
            (c or {}).get('type')
            for c in col.get('constraints') or []
            if (c or {}).get('type')
        ],
    })
  data = {
      'contractEnforced': enforced,
      'modelConstraints': model_constraints,
      'columnContracts': column_contracts,
  }
  checksum = (node.get('contract') or {}).get('checksum')
  if isinstance(checksum, str) and checksum:
    data['contractChecksum'] = checksum[: naming.MAX_LABEL_LENGTH]
  return make_aspect(ctx.aspect_fqn('dbt-model-contracts'), data)
