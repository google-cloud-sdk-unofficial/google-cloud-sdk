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
r"""Per-resource entry builders for the dbt -> Dataplex transform.

One entry is emitted per dbt resource of interest (project, model, source,
seed, snapshot, group, exposure, metric, macro, semantic_model, saved_query,
test). Every entry carries the universal ``dbt-node`` aspect plus its
resource-specific aspect; models/sources/seeds/snapshots additionally carry the
core 1P ``schema`` aspect, tests and source freshness carry
``dbt-data-quality``, and groups/exposures carry the ``contacts`` aspect
required by their entry types. All aspect field names follow the canonical
types verbatim (camelCase).

Entries are also arranged into a hierarchy via ``parentEntry``, rooted at the
project entry::

  dbt-project                                the root
  |- dbt-group                               -> project
  |  |- model / seed / snapshot              -> its group, when declared
  |  |  |- dbt-semantic-model                -> the model it describes
  |  |  \- dbt-test                          -> the resource it tests
  |  \- dbt-metric                           -> its group, when declared
  |- dbt-source                              -> project
  |  \- dbt-test                             -> the source it tests
  |- model / seed / snapshot / dbt-metric    -> project, when ungrouped
  |- dbt-macro / dbt-exposure                -> project
  \- dbt-saved-query                         -> project

Saved queries, metrics and exposures never nest under the resources they
reference: each references N of them and an entry has exactly one parent, so
nesting would assert a relationship dbt does not have. Those stay EntryLinks. A
resource whose parent is ambiguous (a singular test spanning two models) or
unresolvable (an ``attached_node`` naming a resource we don't emit) falls back
to the project, which keeps the tree single-rooted and orphan-free.

Entries are emitted parent-before-child. Batch ingestion does not require that
(the server accepts a child whose parent arrives later in the same job), but
resolving every parent against the already-emitted set is what guarantees no
entry names a parent this job never creates: a dangling ``parentEntry`` is
stored as given rather than rejected, leaving an entry that never surfaces in
the hierarchy. ``parentEntry`` is modifiable on re-ingestion, so re-parenting a
resource -- reassigning a model to another dbt group, say -- lands on the next
import without recreating the entry.
"""

from __future__ import annotations

from collections.abc import Callable
import json
import re
from typing import Any

from googlecloudsdk.command_lib.dataplex.dbt import aspects
from googlecloudsdk.command_lib.dataplex.dbt import naming
from googlecloudsdk.core import log

# Fallback dbt project name when the manifest metadata omits ``project_name``.
_DEFAULT_PROJECT_NAME = 'dbt_project'

_SNAPSHOT_STRATEGY_ENUM = {
    'timestamp': 'TIMESTAMP',
    'check': 'CHECK',
}

_EXPOSURE_TYPE_ENUM = {
    'dashboard': 'DASHBOARD',
    'notebook': 'NOTEBOOK',
    'analysis': 'ANALYSIS',
    'ml': 'ML',
    'application': 'APPLICATION',
}

_EXPOSURE_MATURITY_ENUM = {
    'high': 'HIGH',
    'medium': 'MEDIUM',
    'low': 'LOW',
}


def _set_if(data: dict[str, Any], key: str, value: Any) -> None:
  """Sets ``data[key] = value`` only when ``value`` is truthy."""
  if value:
    data[key] = value


def _normalize_relation(relation: str | None) -> str:
  """Strips an adapter's identifier quoting from a relation name."""
  return re.sub(r'[`"\']', '', relation or '').strip().lower()


def _add_schema_aspect(
    ctx: naming.Context,
    aspects_map: dict[str, Any],
    catalog_columns: dict[str, Any] | None,
    node: dict[str, Any],
    resolve_target: Callable[[str], str | None] | None = None,
    stale_aspects: set[str] | None = None,
) -> None:
  """Adds the core 1P ``schema`` aspect when the resource has any columns.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    aspects_map: the entry's aspect map, updated in place.
    catalog_columns: the catalog node/source ``columns`` mapping, or None.
    node: the dbt resource, read for its manifest columns and constraints.
    resolve_target: maps a foreign key's raw ``to`` to a Dataplex entry name.
    stale_aspects: updated in place with the schema aspect key when the schema
      came from the manifest alone, so an update leaves a stored catalog-backed
      schema as it is.
  """
  columns = aspects.merged_columns(catalog_columns, node.get('columns'))
  if not columns:
    return
  aspects_map[ctx.schema_key()] = aspects.system_schema_aspect(
      ctx, columns, node, resolve_target
  )
  # Without the catalog these columns are the YAML declaration alone: no data
  # types, no nesting, and only the columns the author wrote down. A
  # catalog-backed schema already in the entry must outrank that.
  if stale_aspects is not None and not catalog_columns:
    stale_aspects.add(ctx.schema_key())


def _json_or_empty(value: Any) -> str:
  """Serializes ``value`` to a JSON string, or '' when there is no value.

  Aspect metadata fields use '' as the "absent" sentinel, so ``None`` and empty
  containers/strings map to '' (a bare ``json.dumps`` would instead emit tokens
  like ``'""'`` / ``'null'`` / ``'{}'``). Every other value -- including falsy
  scalars such as ``0`` or ``False`` -- is serialized normally, so the result
  never silently drops a real value regardless of the value's type.

  Args:
    value: the value to serialize (typically a dict, or None).

  Returns:
    The JSON serialization of ``value``, or '' when ``value`` is ``None`` or an
    empty container/string.
  """
  if value is None:
    return ''
  if hasattr(value, '__len__') and not value:
    return ''
  return json.dumps(value, default=str)


# dbt `tags` and `meta` come from hand-written YAML, so a malformed project can
# put a scalar or a list where a mapping belongs. Coerce rather than raise: one
# bad resource should not abort the whole transform.
def _as_list(value: Any) -> list[Any]:
  """Returns ``value`` when it is a list, else an empty list."""
  return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
  """Returns ``value`` when it is a dict, else an empty dict."""
  return value if isinstance(value, dict) else {}


def _compiled_code(node: dict[str, Any]) -> str:
  """Returns a node's compiled SQL, clipped, or '' when it carries none.

  Only a command that compiled the node writes ``compiled_code``; a parse-level
  manifest (what ``dbt parse`` and ``dbt source freshness`` leave behind)
  carries none, and that absence makes the whole payload a downgrade of one
  built from a compiled manifest.

  Args:
    node: the dbt resource to read ``compiled_code`` from.

  Returns:
    The node's compiled SQL, clipped to ``naming.MAX_CODE_BYTES``, or '' when
    the node carries none.
  """
  return _truncate_bytes(node.get('compiled_code'), naming.MAX_CODE_BYTES)


def _set_code(data: dict[str, Any], node: dict[str, Any]) -> None:
  """Copies a node's raw and compiled SQL onto an aspect payload."""
  _set_if(
      data,
      'rawCode',
      _truncate_bytes(node.get('raw_code'), naming.MAX_CODE_BYTES),
  )
  _set_if(data, 'compiledCode', _compiled_code(node))


def _truncate(value: Any, limit: int) -> str:
  """Renders ``value`` as a string clipped to ``limit`` UTF-16 code units.

  The standard library has no UTF-16-aware truncation, so the length is taken
  by encoding. ASCII -- nearly all dbt content, including the SQL bodies that
  are three orders of magnitude longer than any other field here -- takes the
  fast path where the two counts agree and no buffer is allocated.

  Args:
    value: the value to render; ``None`` becomes ''.
    limit: the maximum length in UTF-16 code units.

  Returns:
    The rendered string, clipped so the server will accept it.
  """
  if value is None:
    return ''
  text = str(value)
  if text.isascii():
    return text[:limit]
  # dbt content reaches us straight from JSON, which can carry an unpaired
  # surrogate; surrogatepass keeps that from raising mid-transform.
  encoded = text.encode('utf-16-le', 'surrogatepass')
  if len(encoded) <= limit * 2:
    return text
  # A cut through a surrogate pair leaves half a character; drop it.
  return encoded[: limit * 2].decode('utf-16-le', 'ignore')


def _truncate_bytes(value: Any, limit: int) -> str:
  """Renders ``value`` as a string clipped to ``limit`` UTF-8 bytes."""
  if value is None:
    return ''
  text = str(value)
  if text.isascii():
    # One byte per character, so a character slice is already a byte slice.
    return text[:limit]
  encoded = text.encode('utf-8', 'surrogatepass')
  if len(encoded) <= limit:
    return text
  return encoded[:limit].decode('utf-8', 'ignore')


def _label_value(value: Any) -> str:
  """Renders a dbt `meta` value as a Dataplex label value.

  dbt `meta` is free-form YAML, so a value can be a scalar or a whole nested
  structure. Scalars are rendered as themselves -- including ``0`` and
  ``False``, which are values a reader wants to see, not absences -- and
  anything else is JSON so the catalog does not end up holding a Python repr.

  Args:
    value: the dbt meta value.

  Returns:
    The label value, clipped to the Dataplex label limit.
  """
  if value is None:
    text = ''
  elif isinstance(value, str):
    text = value
  elif isinstance(value, (int, float, bool)):
    text = str(value)
  else:
    text = json.dumps(value, default=str)
  return _truncate(text, naming.MAX_LABEL_LENGTH)


def _resource_labels(resource: dict[str, Any]) -> dict[str, str]:
  """Builds entrySource.labels from a dbt resource's tags and meta.

  dbt tags are a flat list, so each becomes a valueless label; `meta` is
  already key/value. Both can be declared at the top level or under `config`,
  and a resource may carry both, so the two sides are merged with the
  top-level one winning.

  Keys are passed through as the author wrote them. Dataplex validates label
  keys and values for length only (EntryValidator.LABEL_KV_LENGTH_LIMIT).

  Args:
    resource: the dbt resource (node, source, exposure, ...).

  Returns:
    The label map, empty when the resource declares no tags or meta.
  """
  config = _as_dict(resource.get('config'))
  labels = {}
  for tag in _as_list(config.get('tags')) + _as_list(resource.get('tags')):
    key = _truncate(tag, naming.MAX_LABEL_LENGTH)
    if key:
      labels[key] = ''
  meta = {**_as_dict(config.get('meta')), **_as_dict(resource.get('meta'))}
  for key, value in meta.items():
    key = _truncate(key, naming.MAX_LABEL_LENGTH)
    if key:
      labels[key] = _label_value(value)
  return labels


def _entry(
    ctx: naming.Context,
    unique_id: str,
    entry_type: str,
    aspects_map: dict[str, Any],
    fqn: str,
    display_name: str | None = None,
    description: str | None = None,
    labels: dict[str, str] | None = None,
    stale_aspects: set[str] | None = None,
    deleted_aspects: set[str] | None = None,
) -> dict[str, Any]:
  """Wraps an aspect map in the entry record shared by every builder.

  ``stale_aspects`` names aspects whose backing artifact was not part of this
  run, so their payload here is a placeholder rather than an observation. They
  stay in the aspect map -- an entry cannot be created without its required
  aspects -- but are left out of ``aspectKeys``. Creation writes the whole map
  and so still gets them.

  ``deleted_aspects`` is the opposite case: an aspect the resource no longer has
  at all. ``aspectKeys`` is the write mask, so an aspect absent from both the
  map and the mask is not removed -- it keeps whatever an earlier run stored,
  forever. Naming the key without supplying a body deletes it. Only an aspect
  derived from an artifact this run definitely read may be listed here;
  otherwise a run missing that artifact would delete good metadata. A REQUIRED
  aspect must never be listed -- the import job rejects the item.

  How much that protects an existing value depends on the sync mode. Under
  ``--aspects-only`` the write mask is ``aspectKeys`` exactly, so an unobserved
  aspect keeps what is already stored. A full run's mask is ``aspectKeys``
  unioned with the entry type's REQUIRED aspects, so a required one
  (``dbt-model``, ``dbt-seed``, ``dbt-snapshot``, ``dbt-data-quality``) is
  rewritten from the placeholder regardless -- only the optional ``schema``
  aspect is genuinely held back.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    unique_id: the dbt unique_id the entry is named from.
    entry_type: short id of the entry's dbt entry type (e.g. ``dbt-model``).
    aspects_map: the entry's aspects, keyed by aspect key.
    fqn: the entry's fullyQualifiedName.
    display_name: entrySource display name; omitted when None.
    description: entrySource description; omitted when None.
    labels: entrySource labels; omitted when None.
    stale_aspects: aspect keys to leave out of ``aspectKeys``.
    deleted_aspects: aspect keys to name in ``aspectKeys`` without a body, so
      the import deletes whatever is stored under them.

  Returns:
    An import item holding the entry record and its ``aspectKeys``.
  """
  entry_source = {
      # While 'system' is defined in the EntryType, we must populate it here
      # because the backend search service (searchEntries) does not perform
      # fallback to EntryType and requires it to be populated in EntrySource
      # to be indexed and filterable. platform is left unset for now.
      'system': 'DBT',
      'resource': fqn,
  }
  # dbt content is user-authored and unbounded, so clip to the EntrySource
  # limits rather than letting the import job reject the whole entry.
  _set_if(
      entry_source,
      'displayName',
      _truncate(display_name, naming.MAX_DISPLAY_NAME_LENGTH),
  )
  _set_if(
      entry_source,
      'description',
      _truncate(description, naming.MAX_DESCRIPTION_LENGTH),
  )
  _set_if(entry_source, 'labels', labels)
  stale = stale_aspects or set()
  entry = {
      'name': ctx.entry_name(naming.entry_id(unique_id)),
      'entryType': ctx.entry_type(entry_type),
      'aspects': aspects_map,
      'fullyQualifiedName': fqn,
      'entrySource': entry_source,
  }
  keys = {k for k in aspects_map if k not in stale}
  keys.update(deleted_aspects or ())
  return {
      'entry': entry,
      'aspectKeys': sorted(keys),
  }


def _project_unique_id(manifest: dict[str, Any]) -> str:
  """The dbt unique_id of the synthetic project entry."""
  project_name = (
      (manifest.get('metadata') or {}).get('project_name')
      or _DEFAULT_PROJECT_NAME
  )
  return 'project.{0}'.format(project_name)


def _build_project_entry(
    ctx: naming.Context, manifest: dict[str, Any]
) -> dict[str, Any]:
  """Builds the dbt-project entry from the manifest metadata."""
  meta = manifest.get('metadata') or {}
  project_name = meta.get('project_name') or _DEFAULT_PROJECT_NAME
  aspects_map = {
      ctx.aspect_key('dbt-project'): aspects.make_aspect(
          ctx.aspect_fqn('dbt-project'),
          {
              'version': meta.get('dbt_version', ''),
              'dbtProjectName': project_name,
              'adapterType': meta.get('adapter_type', ''),
          },
      ),
  }
  fqn = ctx.dbt_project_fqn(project_name)
  return _entry(
      ctx,
      _project_unique_id(manifest),
      'dbt-project',
      aspects_map,
      fqn,
      display_name=project_name,
  )


def _build_model_entry(
    ctx: naming.Context,
    unique_id: str,
    node: dict[str, Any],
    catalog_nodes: dict[str, Any],
    resolve_target: Callable[[str], str | None] | None = None,
) -> dict[str, Any]:
  """Builds a dbt-model entry with node, model, schema and contract aspects."""
  config = node.get('config') or {}
  cat_node = catalog_nodes.get(unique_id) or {}
  stats = cat_node.get('stats') or {}
  enforced = bool((node.get('contract') or {}).get('enforced', False))

  model_data = {
      'isContractEnforced': enforced,
      'materializationType': config.get('materialized') or '',
  }
  # BigQuery's dbt catalog reports table stats under the `num_rows` /
  # `num_bytes` stat keys (see the dbt-bigquery catalog macro); other adapters
  # use different names (e.g. Snowflake's `row_count` / `bytes`). This connector
  # ingests BigQuery dbt projects, so read the BigQuery keys.
  aspects.add_stat(model_data, 'rowCount', stats, 'num_rows')
  aspects.add_stat(model_data, 'byteCount', stats, 'num_bytes')
  _set_code(model_data, node)
  compiled = bool(_compiled_code(node))

  aspects_map = aspects.base_aspects(
      ctx, unique_id, node, 'model', 'dbt-model', model_data
  )
  stale = set()
  if not cat_node or not compiled:
    stale.add(ctx.aspect_key('dbt-model'))
  _add_schema_aspect(
      ctx,
      aspects_map,
      cat_node.get('columns'),
      node,
      resolve_target,
      stale_aspects=stale,
  )

  contracts = aspects.model_contracts_aspect(ctx, node, enforced)
  contracts_key = ctx.aspect_key('dbt-model-contracts')
  deleted = set()
  if contracts:
    aspects_map[contracts_key] = contracts
  else:
    # Built from the manifest alone, which every run reads, so an absent
    # contract means the model dropped it -- not that this run didn't look.
    deleted.add(contracts_key)

  project_name = node.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = node.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-model', project_name, resource_name)
  return _entry(
      ctx,
      unique_id,
      'dbt-model',
      aspects_map,
      fqn,
      display_name=resource_name,
      description=node.get('description'),
      labels=_resource_labels(node),
      stale_aspects=stale,
      deleted_aspects=deleted,
  )


def _freshness_period(spec: Any) -> str:
  """Renders a dbt freshness threshold {count, period} as e.g. '12 hour'."""
  if not isinstance(spec, dict):
    return ''
  count = spec.get('count')
  period = spec.get('period')
  if count is None or not period:
    return ''
  return '{0} {1}'.format(count, period)


def _build_source_entry(
    ctx: naming.Context,
    unique_id: str,
    src: dict[str, Any],
    sources_map: dict[str, Any],
    catalog_sources: dict[str, Any],
) -> dict[str, Any]:
  """Builds a dbt-source entry (node, source, schema, freshness aspects)."""
  freshness = src.get('freshness') or {}
  source_data = {
      'sourceGroupName': src.get('source_name') or '',
      'tableName': src.get('identifier') or src.get('name') or '',
      'loadedAtField': src.get('loaded_at_field') or '',
      'freshnessWarnAfter': _freshness_period(freshness.get('warn_after')),
      'freshnessErrorAfter': _freshness_period(freshness.get('error_after')),
      'packageName': src.get('package_name') or '',
      'originalFilePath': src.get('original_file_path') or '',
  }
  aspects_map = aspects.base_aspects(
      ctx, unique_id, src, 'source', 'dbt-source', source_data
  )
  cat_source = catalog_sources.get(unique_id) or {}
  stale = set()
  _add_schema_aspect(
      ctx, aspects_map, cat_source.get('columns'), src, stale_aspects=stale
  )

  fresh_res = sources_map.get(unique_id, {})
  if fresh_res:
    dq = {
        'status': fresh_res.get('status') or '',
        'testCategory': 'source',
    }
    _set_if(dq, 'maxLoadedAt', fresh_res.get('max_loaded_at'))
    _set_if(dq, 'snapshottedAt', fresh_res.get('snapshotted_at'))
    aspects_map[ctx.aspect_key('dbt-data-quality')] = aspects.make_aspect(
        ctx.aspect_fqn('dbt-data-quality'), dq
    )

  project_name = src.get('package_name') or _DEFAULT_PROJECT_NAME
  source_name = src.get('source_name') or ''
  table_name = src.get('identifier') or src.get('name') or ''
  fqn = ctx.dbt_source_fqn(project_name, source_name, table_name)
  table_label = src.get('name') or table_name
  return _entry(
      ctx,
      unique_id,
      'dbt-source',
      aspects_map,
      fqn,
      display_name=(
          f'{source_name}.{table_label}' if source_name else table_label
      ),
      description=src.get('description'),
      labels=_resource_labels(src),
      stale_aspects=stale,
  )


def _build_seed_entry(
    ctx: naming.Context,
    unique_id: str,
    node: dict[str, Any],
    catalog_nodes: dict[str, Any],
    resolve_target: Callable[[str], str | None] | None = None,
) -> dict[str, Any]:
  """Builds a dbt-seed entry with node, seed and optional schema aspects."""
  cat_node = catalog_nodes.get(unique_id) or {}
  stats = cat_node.get('stats') or {}
  seed_data = {}
  # See _build_model_entry: BigQuery dbt catalogs key these num_rows/num_bytes.
  aspects.add_stat(seed_data, 'rowCount', stats, 'num_rows')
  aspects.add_stat(seed_data, 'byteCount', stats, 'num_bytes')

  aspects_map = aspects.base_aspects(
      ctx, unique_id, node, 'seed', 'dbt-seed', seed_data
  )
  # dbt-seed holds nothing but catalog stats, so without the catalog it is an
  # empty payload -- exactly what must not be written over a populated one.
  stale = set()
  if not cat_node:
    stale.add(ctx.aspect_key('dbt-seed'))
  _add_schema_aspect(
      ctx,
      aspects_map,
      cat_node.get('columns'),
      node,
      resolve_target=resolve_target,
      stale_aspects=stale,
  )
  project_name = node.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = node.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-seed', project_name, resource_name)
  return _entry(
      ctx,
      unique_id,
      'dbt-seed',
      aspects_map,
      fqn,
      display_name=resource_name,
      description=node.get('description'),
      labels=_resource_labels(node),
      stale_aspects=stale,
  )


def _render_unique_key(unique_key: Any) -> str:
  """Renders a dbt ``unique_key`` (string or list of columns) as a string.

  dbt allows ``unique_key`` to be a single column name or a list of column
  names. A list is joined with commas so it doesn't land in the metadata as a
  Python list repr (e.g. ``"['a', 'b']"``).

  Args:
    unique_key: the dbt config ``unique_key`` value (str, list, or None).

  Returns:
    The unique key as a comma-joined string, or '' when absent.
  """
  if isinstance(unique_key, (list, tuple)):
    return ','.join(str(k) for k in unique_key)
  # Check for None explicitly: a numeric key like 0 is falsy but still a valid
  # unique_key that should render as '0', not ''.
  if unique_key is None:
    return ''
  return str(unique_key)


def _build_snapshot_entry(
    ctx: naming.Context,
    unique_id: str,
    node: dict[str, Any],
    catalog_nodes: dict[str, Any],
    resolve_target: Callable[[str], str | None] | None = None,
) -> dict[str, Any]:
  """Builds a dbt-snapshot entry with node, snapshot and schema aspects."""
  config = node.get('config') or {}
  raw_strategy = config.get('strategy') or ''
  strategy = _SNAPSHOT_STRATEGY_ENUM.get(raw_strategy.lower())
  if raw_strategy and strategy is None:
    log.warning(
        'Unrecognized dbt snapshot strategy [{0}] for [{1}]; the strategy '
        'will be omitted from the dbt-snapshot aspect. Expected one of: '
        '{2}.'.format(
            raw_strategy, unique_id, ', '.join(sorted(_SNAPSHOT_STRATEGY_ENUM))
        )
    )

  check_cols = []
  if strategy == 'CHECK':
    check_cols = config.get('check_cols') or []
    if isinstance(check_cols, str):
      check_cols = [check_cols]

  data = {
      'uniqueKey': _render_unique_key(config.get('unique_key')),
      # str() guards against a malformed config carrying a non-string value.
      'updatedAt': str(config.get('updated_at') or ''),
      'checkCols': check_cols,
      'targetSchema': node.get('schema') or '',
  }
  _set_if(data, 'strategy', strategy)
  _set_code(data, node)
  compiled = bool(_compiled_code(node))

  aspects_map = aspects.base_aspects(
      ctx, unique_id, node, 'snapshot', 'dbt-snapshot', data
  )
  stale = set()
  if not compiled:
    stale.add(ctx.aspect_key('dbt-snapshot'))
  cat_node = catalog_nodes.get(unique_id) or {}
  _add_schema_aspect(
      ctx,
      aspects_map,
      cat_node.get('columns'),
      node,
      resolve_target=resolve_target,
      stale_aspects=stale,
  )
  project_name = node.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = node.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-snapshot', project_name, resource_name)
  return _entry(
      ctx,
      unique_id,
      'dbt-snapshot',
      aspects_map,
      fqn,
      display_name=resource_name,
      description=node.get('description'),
      labels=_resource_labels(node),
      stale_aspects=stale,
  )


def _build_group_entry(
    ctx: naming.Context,
    unique_id: str,
    group: dict[str, Any],
    group_map: dict[str, Any],
) -> dict[str, Any]:
  """Builds a dbt-group entry with node, group and contacts aspects."""
  group_name = group.get('name') or ''
  config = group.get('config') or {}
  identities = aspects.owner_identities(group.get('owner'))

  aspects_map = {
      ctx.aspect_key('dbt-node'): aspects.node_aspect(
          ctx, unique_id, group, 'group'
      ),
      ctx.aspect_key('dbt-group'): aspects.make_aspect(
          ctx.aspect_fqn('dbt-group'),
          {
              'packageName': group.get('package_name') or '',
              'config': _json_or_empty(config),
              'governedResourcesCount': len(group_map.get(group_name, [])),
          },
      ),
      # contacts is a required aspect on the dbt-group entry type.
      ctx.contacts_key(): aspects.contacts_aspect(ctx, identities),
  }
  project_name = group.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = group.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-group', project_name, resource_name)
  return _entry(
      ctx,
      unique_id,
      'dbt-group',
      aspects_map,
      fqn,
      display_name=resource_name,
      description=group.get('description'),
      labels=_resource_labels(group),
  )


def _build_exposure_entry(
    ctx: naming.Context, unique_id: str, exposure: dict[str, Any]
) -> dict[str, Any]:
  """Builds a dbt-exposure entry with node, exposure and contacts aspects."""
  identities = aspects.owner_identities(exposure.get('owner'))

  exposure_data = {
      'url': exposure.get('url') or '',
      'packageName': exposure.get('package_name') or '',
      'originalFilePath': exposure.get('original_file_path') or '',
  }
  exposure_type = (exposure.get('type') or '').lower()
  if exposure_type in _EXPOSURE_TYPE_ENUM:
    exposure_data['exposureType'] = _EXPOSURE_TYPE_ENUM[exposure_type]
  maturity = (exposure.get('maturity') or '').lower()
  if maturity in _EXPOSURE_MATURITY_ENUM:
    exposure_data['maturity'] = _EXPOSURE_MATURITY_ENUM[maturity]

  aspects_map = {
      ctx.aspect_key('dbt-node'): aspects.node_aspect(
          ctx, unique_id, exposure, 'exposure'
      ),
      ctx.aspect_key('dbt-exposure'): aspects.make_aspect(
          ctx.aspect_fqn('dbt-exposure'), exposure_data
      ),
      # contacts is a required aspect on the dbt-exposure entry type.
      ctx.contacts_key(): aspects.contacts_aspect(ctx, identities),
  }
  project_name = exposure.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = exposure.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-exposure', project_name, resource_name)
  return _entry(
      ctx,
      unique_id,
      'dbt-exposure',
      aspects_map,
      fqn,
      display_name=exposure.get('label') or resource_name,
      description=exposure.get('description'),
      labels=_resource_labels(exposure),
  )


def _where_clause(where: Any) -> str:
  """Renders a dbt where/filter spec as a SQL string.

  Handles both shapes dbt uses for the "where" concept -- a saved query's
  ``query_params.where`` and a metric's ``filter`` -- which are the same
  structure: either a bare SQL string, or ``{'where_filters': [{'
  where_sql_template': ...}, ...]}`` whose templates are ANDed together.

  Args:
    where: the dbt where/filter value (str, dict, or None).

  Returns:
    The combined SQL string, or '' when absent / unrecognized.
  """
  if not where:
    return ''
  if isinstance(where, str):
    return where
  if isinstance(where, dict):
    templates = [
        f.get('where_sql_template', '')
        for f in where.get('where_filters') or []
    ]
    return ' AND '.join(t for t in templates if t)
  return ''


def _build_metric_entry(
    ctx: naming.Context,
    unique_id: str,
    metric: dict[str, Any],
) -> dict[str, Any]:
  """Builds a dbt-metric entry with node and metric aspects."""
  type_params = metric.get('type_params') or {}
  input_measures = type_params.get('input_measures') or []
  base_measures = [m.get('name') for m in input_measures if m.get('name')]
  meta = metric.get('meta') or {}
  filt = metric.get('filter')

  aspects_map = {
      ctx.aspect_key('dbt-node'): aspects.node_aspect(
          ctx, unique_id, metric, 'metric'
      ),
      ctx.aspect_key('dbt-metric'): aspects.make_aspect(
          ctx.aspect_fqn('dbt-metric'),
          {
              'label': metric.get('label') or '',
              'metricType': metric.get('type') or '',
              'typeParams': _json_or_empty(type_params),
              # A dbt metric `filter` nests its SQL under `where_filters`, the
              # same shape as a saved query's `where`; reuse the one parser.
              'baseFilter': _where_clause(filt),
              'timeGranularity': metric.get('time_granularity') or '',
              'baseMeasures': base_measures,
              'metadata': _json_or_empty(meta),
          },
      ),
  }
  project_name = metric.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = metric.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-metric', project_name, resource_name)
  return _entry(
      ctx,
      unique_id,
      'dbt-metric',
      aspects_map,
      fqn,
      display_name=metric.get('label') or resource_name,
      description=metric.get('description'),
      labels=_resource_labels(metric),
  )


def _build_macro_entry(
    ctx: naming.Context, unique_id: str, macro: dict[str, Any]
) -> dict[str, Any]:
  """Builds a dbt-macro entry with node and macro aspects."""
  args = []
  for arg in macro.get('arguments') or []:
    args.append({
        'name': arg.get('name') or '',
        'type': arg.get('type') or '',
        'description': arg.get('description') or '',
    })
  aspects_map = {
      ctx.aspect_key('dbt-node'): aspects.node_aspect(
          ctx, unique_id, macro, 'macro'
      ),
      ctx.aspect_key('dbt-macro'): aspects.make_aspect(
          ctx.aspect_fqn('dbt-macro'),
          {
              'macroSql': _truncate_bytes(
                  macro.get('macro_sql'), naming.MAX_CODE_BYTES
              ),
              'arguments': args,
          },
      ),
  }
  project_name = macro.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = macro.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-macro', project_name, resource_name)
  return _entry(
      ctx,
      unique_id,
      'dbt-macro',
      aspects_map,
      fqn,
      display_name=resource_name,
      description=macro.get('description'),
      labels=_resource_labels(macro),
  )


def _build_semantic_model_entry(
    ctx: naming.Context,
    unique_id: str,
    sm: dict[str, Any],
) -> dict[str, Any]:
  """Builds a dbt-semantic-model entry with node and semantic-model aspects."""
  relation = sm.get('node_relation') or {}
  default_time_dim = (sm.get('defaults') or {}).get('agg_time_dimension')

  measures = [
      {
          'name': m.get('name', ''),
          'description': m.get('description') or '',
          'aggType': m.get('agg', ''),
          'expression': m.get('expr') or '',
          'params': _json_or_empty(m.get('agg_params')),
      }
      for m in sm.get('measures') or []
  ]
  dimensions = [
      {
          'name': d.get('name', ''),
          'description': d.get('description') or '',
          'type': d.get('type', ''),
          'expression': d.get('expr') or '',
          'params': _json_or_empty(d.get('type_params')),
          'isDefaultTimeDimension': d.get('name') == default_time_dim,
      }
      for d in sm.get('dimensions') or []
  ]
  entities = [
      {
          'name': e.get('name', ''),
          'type': e.get('type', ''),
          'expression': e.get('expr') or '',
      }
      for e in sm.get('entities') or []
  ]

  aspects_map = {
      ctx.aspect_key('dbt-node'): aspects.node_aspect(
          ctx,
          unique_id,
          sm,
          'semantic_model',
          database=relation.get('database'),
          namespace=relation.get('schema_name'),
      ),
      ctx.aspect_key('dbt-semantic-model'): aspects.make_aspect(
          ctx.aspect_fqn('dbt-semantic-model'),
          {
              'modelReference': sm.get('model') or '',
              'entities': entities,
              'measures': measures,
              'dimensions': dimensions,
          },
      ),
  }
  project_name = sm.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = sm.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-semantic-model', project_name, resource_name)
  return _entry(
      ctx,
      unique_id,
      'dbt-semantic-model',
      aspects_map,
      fqn,
      display_name=sm.get('label') or resource_name,
      description=sm.get('description'),
      labels=_resource_labels(sm),
  )


def _build_saved_query_entry(
    ctx: naming.Context, unique_id: str, sq: dict[str, Any]
) -> dict[str, Any]:
  """Builds a dbt-saved-query entry with node and saved-query aspects."""
  qp = sq.get('query_params') or {}
  exports = []
  for ex in sq.get('exports') or []:
    ex_config = ex.get('config') or {}
    export_as = ex_config.get('export_as') or 'table'
    exports.append({
        'name': ex.get('name', ''),
        'materializationType': export_as,
        # dbt's *rendered* export config carries the target schema under
        # `schema_name`; `schema` only survives in `unrendered_config`. Prefer
        # the rendered key, falling back to the raw one.
        'namespace': (
            ex_config.get('schema_name') or ex_config.get('schema') or ''
        ),
        'alias': ex_config.get('alias') or '',
    })

  sq_data = {
      'queryMetrics': qp.get('metrics') or [],
      'groupBy': qp.get('group_by') or [],
      'whereClause': _where_clause(qp.get('where')),
      'exports': exports,
      'metadata': _json_or_empty((sq.get('config') or {}).get('meta')),
      'orderBy': [
          o if isinstance(o, str) else json.dumps(o, default=str)
          for o in qp.get('order_by') or []
      ],
  }
  limit = qp.get('limit')
  if isinstance(limit, int) and not isinstance(limit, bool):
    sq_data['limit'] = limit

  aspects_map = {
      ctx.aspect_key('dbt-node'): aspects.node_aspect(
          ctx, unique_id, sq, 'saved_query'
      ),
      ctx.aspect_key('dbt-saved-query'): aspects.make_aspect(
          ctx.aspect_fqn('dbt-saved-query'), sq_data
      ),
  }
  project_name = sq.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = sq.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-saved-query', project_name, resource_name)
  return _entry(
      ctx,
      unique_id,
      'dbt-saved-query',
      aspects_map,
      fqn,
      display_name=sq.get('label') or resource_name,
      description=sq.get('description'),
      labels=_resource_labels(sq),
  )


# The statuses dbt reports for a test
# (dbt.artifacts.schemas.results.TestStatus). Every other command shares
# run_results.json with a status drawn from a different enum -- notably
# `dbt compile` and, before Fusion dropped the command, `dbt docs generate`,
# both of which record every test as the RunStatus `success`. Reading that back
# as a test outcome reports the whole suite as having succeeded whether or not
# it ever ran, so a status outside this set is treated as "this run carries no
# verdict for this test".
_TEST_STATUSES = frozenset(['pass', 'fail', 'warn', 'error', 'skipped'])

# dbt commands that never execute a test. `error` and `skipped` exist in both
# enums, so the status alone cannot tell a compile-time outcome from a real
# verdict; the command that wrote the file can.
_NON_TESTING_COMMANDS = frozenset(['compile', 'docs', 'generate', 'parse'])


def _run_carries_test_verdicts(run_results: dict[str, Any] | None) -> bool:
  """Whether the command that wrote ``run_results`` could have run tests."""
  which = ((run_results or {}).get('args') or {}).get('which')
  return not (isinstance(which, str) and which.lower() in _NON_TESTING_COMMANDS)


def _test_result(res: dict[str, Any]) -> dict[str, Any]:
  """Returns ``res`` when it holds a genuine test verdict, else empty."""
  status = res.get('status')
  is_verdict = isinstance(status, str) and status.lower() in _TEST_STATUSES
  return res if is_verdict else {}


def _test_category(test_node: dict[str, Any]) -> str:
  """Classifies a dbt test for dbt-data-quality.testCategory."""
  test_metadata = test_node.get('test_metadata') or {}
  if test_metadata.get('name'):
    return test_metadata.get('name')  # generic: unique, not_null, ...
  return 'singular'  # bespoke SQL test


def _build_test_entry(
    ctx: naming.Context,
    unique_id: str,
    test_node: dict[str, Any],
    run_results_map: dict[str, Any],
) -> dict[str, Any]:
  """Builds a dbt-test entry with node and data-quality aspects."""
  config = test_node.get('config') or {}
  test_metadata = test_node.get('test_metadata') or {}
  kwargs = test_metadata.get('kwargs') or {}
  res = run_results_map.get(unique_id, {})
  # res still supplies the compiled SQL even when it carries no verdict: a
  # compile run's SQL is as good as a test run's, only its status is not.
  verdict = _test_result(res)

  dq = {
      'columnName': (
          test_node.get('column_name') or kwargs.get('column_name') or ''
      ),
      # The compiled test SQL is written to run_results.json; the manifest node
      # only carries it when the manifest was produced by `dbt compile`.
      'sqlDefinition': _truncate_bytes(
          res.get('compiled_code')
          or test_node.get('compiled_code')
          or test_node.get('compiled_sql'),
          naming.MAX_CODE_BYTES,
      ),
      'severity': config.get('severity') or '',
      'storeFailures': bool(config.get('store_failures', False)),
      'status': verdict.get('status') or '',
      'testCategory': _test_category(test_node),
      'message': verdict.get('message') or '',
  }
  failures = verdict.get('failures')
  if isinstance(failures, int):
    dq['failures'] = failures
  rows_affected = (verdict.get('adapter_response') or {}).get('rows_affected')
  if isinstance(rows_affected, int):
    dq['rowsAffected'] = rows_affected

  aspects_map = {
      ctx.aspect_key('dbt-node'): aspects.node_aspect(
          ctx, unique_id, test_node, 'test'
      ),
      ctx.aspect_key('dbt-data-quality'): aspects.make_aspect(
          ctx.aspect_fqn('dbt-data-quality'), dq
      ),
  }
  stale = set() if verdict else {ctx.aspect_key('dbt-data-quality')}
  project_name = test_node.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = test_node.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-test', project_name, resource_name)
  return _entry(
      ctx,
      unique_id,
      'dbt-test',
      aspects_map,
      fqn,
      display_name=resource_name,
      description=test_node.get('description'),
      labels=_resource_labels(test_node),
      stale_aspects=stale,
  )


def _check_size_limits(
    ctx: naming.Context, unique_id: str, record: dict[str, Any]
) -> None:
  """Fails the transform when an entry or aspect exceeds a Dataplex size limit.

  dbt resources carry arbitrary user content (compiled test SQL, macro bodies,
  very wide schemas, free-form ``meta`` blobs), so a single aspect or a whole
  entry can outgrow the sizes the import job accepts. The import job would
  reject such an item server-side, so we fail here -- before the file is copied
  to GCS and an import job is started -- and point at the offending resource.
  See https://cloud.google.com/dataplex/docs/quotas#limits.

  The schema aspect is the exception: a wide or deeply nested schema is normal
  dbt output rather than a mistake, so it is trimmed to the column and byte
  budgets and the resource is imported without its tail columns. Every other
  aspect holds content we cannot shorten without losing its meaning, so those
  still fail the run.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    unique_id: the dbt unique_id of the resource, for the error message.
    record: the entry record built for the resource.

  Raises:
    naming.TransformError: if a non-schema aspect exceeds the per-aspect limit,
      or the whole entry exceeds the per-entry limit.
  """
  entry = record['entry']
  schema_key = ctx.schema_key()
  schema = entry['aspects'].get(schema_key)
  if schema:
    fields = schema.get('data', {}).get('fields') or []
    before = aspects.count_fields(fields)
    fitted = aspects.fit_fields(
        fields,
        naming.MAX_SCHEMA_COLUMNS,
        naming.MAX_SCHEMA_ASPECT_JSON_BYTES,
    )
    after = aspects.count_fields(fitted)
    if after < before:
      schema['data']['fields'] = fitted
      log.warning(
          f'dbt resource [{unique_id}] has a schema too large for the '
          f'catalog; keeping {after} of {before} columns. The rest are '
          'omitted from the schema aspect.'
      )
  for key, aspect in entry['aspects'].items():
    if key == schema_key:
      continue
    aspect_bytes = len(json.dumps(aspect.get('data', {})).encode('utf-8'))
    if aspect_bytes > naming.MAX_ASPECT_JSON_BYTES:
      raise naming.TransformError(
          f'Aspect [{key}] on dbt resource [{unique_id}] is '
          f'{aspect_bytes // 1024} KB, over the '
          f'{naming.MAX_ASPECT_JSON_BYTES // 1024} KB per-aspect limit, and '
          "would be rejected by the import job. Reduce the resource's content "
          '(e.g. compiled SQL, macro body) and re-run.'
      )
  entry_bytes = len(json.dumps(entry).encode('utf-8'))
  if entry_bytes > naming.MAX_ENTRY_BYTES:
    raise naming.TransformError(
        f'dbt resource [{unique_id}] builds a {entry_bytes // 1024} KB entry, '
        f'over the {naming.MAX_ENTRY_BYTES // 1024} KB entry size limit, and '
        "would be rejected by the import job. Reduce the resource's content "
        'and re-run.'
    )


def _sole_dependency(node: dict[str, Any]) -> str | None:
  """The node's single upstream dbt node, or None when it isn't exactly one."""
  deps = (node.get('depends_on') or {}).get('nodes') or []
  return deps[0] if len(deps) == 1 else None


def model_uids_by_name(nodes: dict[str, Any]) -> dict[str, str]:
  """Indexes the manifest's models by name, for resolving a ``ref()`` target.

  Args:
    nodes: the manifest ``nodes`` section.

  Returns:
    A dict of model name -> unique_id, over models only. A name carried by more
    than one model (versioned models, or two packages defining the same name) is
    left out rather than resolved to an arbitrary one of them.
  """
  index: dict[str, str] = {}
  ambiguous = set()
  for uid, node in nodes.items():
    if node.get('resource_type') != 'model':
      continue
    name = node.get('name')
    if not name:
      continue
    if name in index:
      ambiguous.add(name)
      continue
    index[name] = uid
  for name in ambiguous:
    del index[name]
  return index


def described_model(
    sm: dict[str, Any], model_uid_by_name: dict[str, str]
) -> str | None:
  """The unique_id of the one model a semantic model describes.

  A semantic model declares its model as ``model: ref('orders')``. That is the
  authoritative link; ``depends_on`` is derived and can pick up a second node
  (a filter referencing another model, say), which would make the relationship
  ambiguous even though dbt named it outright.

  Args:
    sm: the dbt semantic model.
    model_uid_by_name: model name -> unique_id, from ``model_uids_by_name``.

  Returns:
    The backing model's unique_id, or None when it cannot be resolved.
  """
  declared = model_uid_by_name.get(naming.parse_ref(sm.get('model')) or '')
  # A ``ref()`` carries only a short name, so accept the resolution only when
  # dbt's own dependency graph agrees the semantic model reads that node.
  if declared:
    depends_on = (sm.get('depends_on') or {}).get('nodes') or []
    if not depends_on or declared in depends_on:
      return declared
  return _sole_dependency(sm)


def _test_parent_id(test_node: dict[str, Any]) -> str | None:
  """The dbt resource a test hangs off, or None when it is ambiguous.

  Generic tests (unique, not_null, ...) name their subject in
  ``attached_node``. Singular tests do not, so fall back to their dependency
  when there is exactly one -- a relationship test spanning two models has no
  single owner and stays at the project root.

  Args:
    test_node: the dbt test node.

  Returns:
    The dbt unique_id of the tested resource, or None.
  """
  return test_node.get('attached_node') or _sole_dependency(test_node)


def _index_by_unique_id(
    results: list[dict[str, Any]] | None,
) -> dict[str, Any]:
  """Indexes a list of dbt result rows by unique_id, skipping malformed rows.

  Unlike the rest of the manifest, the run_results / sources result rows are
  read here into a lookup; a row missing ``unique_id`` is skipped rather than
  raising, so a partially-written artifact degrades gracefully.

  Args:
    results: the list of dbt result rows (run_results / sources ``results``).

  Returns:
    A dict of dbt unique_id -> result row.
  """
  if not results:
    return {}
  index = {}
  for row in results:
    uid = row.get('unique_id')
    if uid:
      index[uid] = row
  return index


def build_entries(
    ctx: naming.Context,
    manifest: dict[str, Any],
    catalog: dict[str, Any] | None = None,
    run_results: dict[str, Any] | None = None,
    sources: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], set[str]]:
  """Builds every dbt entry record from the parsed artifacts.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the parsed dbt manifest.json.
    catalog: the parsed dbt catalog.json, or None/{} when the optional artifact
      is absent.
    run_results: the parsed dbt run_results.json, or None/{} when the optional
      artifact is absent.
    sources: the parsed dbt sources.json, or None/{} when the optional artifact
      is absent.

  Returns:
    (entries, known_ids): the entry records, and the set of Dataplex entry ids
    they occupy. entry_links consumes the id set directly instead of parsing
    ids back out of the entry resource names.

  Raises:
    naming.TransformError: if any entry or aspect exceeds the Dataplex size
      limits, so the run fails before the import file is uploaded.
  """
  project_name = (
      manifest.get('metadata') or {}
  ).get('project_name') or _DEFAULT_PROJECT_NAME
  nodes = manifest.get('nodes') or {}
  manifest_sources = manifest.get('sources') or {}
  catalog_nodes = (catalog or {}).get('nodes') or {}
  catalog_sources = (catalog or {}).get('sources') or {}
  group_map = manifest.get('group_map') or {}
  run_results_map = _index_by_unique_id((run_results or {}).get('results'))
  if not _run_carries_test_verdicts(run_results):
    # Keep the compiled SQL, drop the status: a command that ran no test still
    # writes one, and `error` / `skipped` look like verdicts.
    run_results_map = {
        uid: {k: v for k, v in res.items() if k != 'status'}
        for uid, res in run_results_map.items()
    }
  sources_map = _index_by_unique_id((sources or {}).get('results'))
  groups = manifest.get('groups') or {}
  # dbt nodes name their group by name; the group entry is keyed by unique_id.
  # A group without a name is skipped, so that an ungrouped node -- which also
  # resolves to no name -- does not match it.
  group_uid_by_name = {
      group['name']: unique_id
      for unique_id, group in groups.items()
      if group.get('name')
  }
  by_type = {'model': [], 'seed': [], 'snapshot': [], 'test': []}
  for unique_id, node in nodes.items():
    bucket = by_type.get(node.get('resource_type'))
    if bucket is not None:
      bucket.append((unique_id, node))

  # A foreign_key constraint's target reaches the manifest in one of two forms:
  # the authored `to: ref('model')`, or -- once the model's contract is
  # enforced, which is when dbt renders the constraint into DDL -- the resolved
  # relation name (`` `project`.`dataset`.`model` ``). Both are indexed, since
  # the 1P schema aspect wants a Dataplex entry name either way. Index by short
  # name rather than rebuilding the unique_id, for the reasons in entry_links.
  # Foreign key resolution is best effort: dbt's `to` is free text, so a target
  # can be a ref(), a bare relation, a source() or something we don't model at
  # all. Anything that does not resolve to exactly one node is left off the
  # constraint rather than guessed at -- a wrong `referencedTable` reads as
  # authoritative lineage, which is worse than none.
  uid_by_name = {}
  uid_by_relation = {}
  ambiguous_names = set()
  ambiguous_relations = set()
  for unique_id, node in nodes.items():
    if node.get('resource_type') not in ('model', 'seed', 'snapshot'):
      continue
    name = node.get('name')
    if name:
      # Versioned models share a name, as do two packages defining the same one.
      if name in uid_by_name:
        ambiguous_names.add(name)
      else:
        uid_by_name[name] = unique_id
    relation = _normalize_relation(node.get('relation_name'))
    if relation:
      if relation in uid_by_relation:
        ambiguous_relations.add(relation)
      else:
        uid_by_relation[relation] = unique_id
  for name in ambiguous_names:
    del uid_by_name[name]
  for relation in ambiguous_relations:
    del uid_by_relation[relation]

  entries = []
  # entry_id -> unique_id, tracked as entries are added. This hands entry_links
  # a ready id set and lets us warn when the lossy unique_id -> entry_id mapping
  # (naming.entry_id lowercases and replaces dots) collapses two distinct
  # resources onto one id -- one would silently overwrite the other on import.
  ids = {}

  # dbt unique_ids already emitted. `parentEntry` is validated against an
  # existing entry at create time, so a parent is only attached once we have
  # actually emitted it -- which the emission order below guarantees.
  emitted = set()
  project_id = _project_unique_id(manifest)

  def add(
      unique_id: str,
      record: dict[str, Any],
      parent_unique_id: str | None = None,
  ) -> None:
    # A parent that was never emitted -- an `attached_node` naming a resource
    # type we don't emit, say -- would be a dangling reference that Dataplex
    # rejects, so fall back to the project to keep the tree connected. The
    # project itself is the root and takes no parent.
    parent = parent_unique_id if parent_unique_id in emitted else project_id
    if parent != unique_id:
      record['entry']['parentEntry'] = ctx.entry_name(naming.entry_id(parent))
    emitted.add(unique_id)
    entries.append(record)
    entry_id = naming.entry_id(unique_id)
    if len(entry_id) > naming.MAX_ENTRY_ID_LENGTH:
      log.warning(
          'Dataplex entry id [{0}] for dbt resource [{1}] exceeds the '
          '{2}-character limit and will be rejected on import.'.format(
              entry_id, unique_id, naming.MAX_ENTRY_ID_LENGTH
          )
      )
    _check_size_limits(ctx, unique_id, record)
    if entry_id in ids and ids[entry_id] != unique_id:
      log.warning(
          'Two dbt resources map to the same Dataplex entry id [{0}] ([{1}] '
          'and [{2}]); one will overwrite the other on import.'.format(
              entry_id, ids[entry_id], unique_id
          )
      )
    ids[entry_id] = unique_id

  def group_uid(node: dict[str, Any]) -> str | None:
    """The unique_id of the node's dbt group, when it declares one."""
    name = node.get('group') or (node.get('config') or {}).get('group')
    return group_uid_by_name.get(name) if name else None

  def resolve_target(to: str) -> str | None:
    """Maps a foreign key's raw `to` to its Dataplex entry name, if any."""
    target = uid_by_name.get(naming.parse_ref(to) or '')
    if not target:
      target = uid_by_relation.get(_normalize_relation(to))
    return ctx.entry_name(naming.entry_id(target)) if target else None

  # Emission order is the hierarchy order: a parent is always written before
  # its children so that `parentEntry` resolves at import time.
  add(project_id, _build_project_entry(ctx, manifest))

  for unique_id, group in groups.items():
    add(
        unique_id,
        _build_group_entry(ctx, unique_id, group, group_map),
        project_id,
    )

  for unique_id, src in manifest_sources.items():
    add(
        unique_id,
        _build_source_entry(ctx, unique_id, src, sources_map, catalog_sources),
        project_id,
    )

  for unique_id, exposure in (manifest.get('exposures') or {}).items():
    add(unique_id, _build_exposure_entry(ctx, unique_id, exposure), project_id)

  # A metric declares dbt group membership the same way a model does.
  for unique_id, metric in (manifest.get('metrics') or {}).items():
    add(
        unique_id,
        _build_metric_entry(ctx, unique_id, metric),
        group_uid(metric),
    )

  for unique_id, sq in (manifest.get('saved_queries') or {}).items():
    add(unique_id, _build_saved_query_entry(ctx, unique_id, sq), project_id)

  for unique_id, macro in (manifest.get('macros') or {}).items():
    # Only emit macros defined in the user's project (not imported packages).
    if macro.get('package_name') != project_name:
      continue
    add(unique_id, _build_macro_entry(ctx, unique_id, macro), project_id)

  # Materialized resources nest under their dbt group when they declare one.
  model_uid_by_name = model_uids_by_name(nodes)
  for unique_id, node in by_type['model']:
    add(
        unique_id,
        _build_model_entry(ctx, unique_id, node, catalog_nodes, resolve_target),
        group_uid(node),
    )
  for unique_id, node in by_type['seed']:
    add(
        unique_id,
        _build_seed_entry(ctx, unique_id, node, catalog_nodes, resolve_target),
        group_uid(node),
    )
  for unique_id, node in by_type['snapshot']:
    add(
        unique_id,
        _build_snapshot_entry(
            ctx, unique_id, node, catalog_nodes, resolve_target
        ),
        group_uid(node),
    )

  # A semantic model describes exactly one physical model, which is the most
  # informative parent; failing that, the group it declares, then the project.
  for unique_id, sm in (manifest.get('semantic_models') or {}).items():
    model_uid = described_model(sm, model_uid_by_name)
    add(
        unique_id,
        _build_semantic_model_entry(ctx, unique_id, sm),
        model_uid if model_uid in emitted else group_uid(sm),
    )

  # Tests hang off the resource they test.
  for unique_id, node in by_type['test']:
    add(
        unique_id,
        _build_test_entry(ctx, unique_id, node, run_results_map),
        _test_parent_id(node),
    )

  return entries, set(ids)
