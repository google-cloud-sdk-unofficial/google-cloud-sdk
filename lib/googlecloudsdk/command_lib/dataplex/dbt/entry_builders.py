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
"""Per-resource entry builders for the dbt -> Dataplex transform.

One entry is emitted per dbt resource of interest (project, model, source,
seed, snapshot, group, exposure, metric, macro, semantic_model, saved_query,
test). Every entry carries the universal ``dbt-node`` aspect plus its
resource-specific aspect; models/sources/seeds additionally carry the optional
``dbt-schema`` aspect, tests and source freshness carry ``dbt-data-quality``,
and groups/exposures carry the ``contacts`` aspect required by their entry
types. All aspect field names follow the canonical types verbatim (camelCase).
"""

from __future__ import annotations

import json
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


def _add_schema_aspect(
    ctx: naming.Context,
    aspects_map: dict[str, Any],
    columns: dict[str, Any],
    type_key: str,
    desc_key: str,
) -> None:
  """Adds a dbt-schema aspect to ``aspects_map`` when ``columns`` is set."""
  if columns:
    aspects_map[ctx.aspect_key('dbt-schema')] = (
        aspects.schema_aspect_from_columns(ctx, columns, type_key, desc_key)
    )


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


def _entry(
    ctx: naming.Context,
    unique_id: str,
    entry_type: str,
    aspects_map: dict[str, Any],
    fqn: str,
) -> dict[str, Any]:
  """Wraps an aspect map in the entry record shared by every builder."""
  return {
      'entry': {
          'name': ctx.entry_name(naming.entry_id(unique_id)),
          'entryType': ctx.entry_type(entry_type),
          'aspects': aspects_map,
          'fullyQualifiedName': fqn,
          # Populate entrySource fields.
          # While 'system' is defined in the EntryType, we must populate it here
          # because the backend search service (searchEntries) does not perform
          # fallback to EntryType and requires it to be populated in EntrySource
          # to be indexed and filterable. platform is left unset for now.
          'entrySource': {
              'system': 'DBT',
              'resource': unique_id,
          },
      }
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
      ctx, _project_unique_id(manifest), 'dbt-project', aspects_map, fqn
  )


def _build_model_entry(
    ctx: naming.Context,
    unique_id: str,
    node: dict[str, Any],
    catalog_nodes: dict[str, Any],
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
  aspects.add_stat(model_data, 'rowCount', stats, 'row_count')
  aspects.add_stat(model_data, 'byteCount', stats, 'bytes')

  aspects_map = aspects.base_aspects(
      ctx, unique_id, node, 'model', 'dbt-model', model_data
  )
  _add_schema_aspect(
      ctx, aspects_map, cat_node.get('columns', {}), 'type', 'comment'
  )

  contracts = aspects.model_contracts_aspect(ctx, node, enforced)
  if contracts:
    aspects_map[ctx.aspect_key('dbt-model-contracts')] = contracts

  project_name = node.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = node.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-model', project_name, resource_name)
  return _entry(ctx, unique_id, 'dbt-model', aspects_map, fqn)


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
  _add_schema_aspect(
      ctx, aspects_map, src.get('columns', {}), 'data_type', 'description'
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
  return _entry(ctx, unique_id, 'dbt-source', aspects_map, fqn)


def _build_seed_entry(
    ctx: naming.Context,
    unique_id: str,
    node: dict[str, Any],
    catalog_nodes: dict[str, Any],
) -> dict[str, Any]:
  """Builds a dbt-seed entry with node, seed and optional schema aspects."""
  cat_node = catalog_nodes.get(unique_id) or {}
  stats = cat_node.get('stats') or {}
  seed_data = {}
  aspects.add_stat(seed_data, 'rowCount', stats, 'row_count')
  aspects.add_stat(seed_data, 'byteCount', stats, 'bytes')

  aspects_map = aspects.base_aspects(
      ctx, unique_id, node, 'seed', 'dbt-seed', seed_data
  )
  _add_schema_aspect(
      ctx, aspects_map, cat_node.get('columns', {}), 'type', 'comment'
  )
  project_name = node.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = node.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-seed', project_name, resource_name)
  return _entry(ctx, unique_id, 'dbt-seed', aspects_map, fqn)


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
    ctx: naming.Context, unique_id: str, node: dict[str, Any]
) -> dict[str, Any]:
  """Builds a dbt-snapshot entry with node and snapshot aspects."""
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

  aspects_map = aspects.base_aspects(
      ctx, unique_id, node, 'snapshot', 'dbt-snapshot', data
  )
  project_name = node.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = node.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-snapshot', project_name, resource_name)
  return _entry(ctx, unique_id, 'dbt-snapshot', aspects_map, fqn)


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
  return _entry(ctx, unique_id, 'dbt-group', aspects_map, fqn)


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
  return _entry(ctx, unique_id, 'dbt-exposure', aspects_map, fqn)


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
    ctx: naming.Context, unique_id: str, metric: dict[str, Any]
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
              'typeParams': json.dumps(type_params, default=str),
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
  return _entry(ctx, unique_id, 'dbt-metric', aspects_map, fqn)


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
              'macroSql': macro.get('macro_sql') or '',
              'arguments': args,
          },
      ),
  }
  project_name = macro.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = macro.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-macro', project_name, resource_name)
  return _entry(ctx, unique_id, 'dbt-macro', aspects_map, fqn)


def _build_semantic_model_entry(
    ctx: naming.Context, unique_id: str, sm: dict[str, Any]
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
  return _entry(ctx, unique_id, 'dbt-semantic-model', aspects_map, fqn)


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
        'namespace': ex_config.get('schema') or '',
        'alias': ex_config.get('alias') or '',
    })

  aspects_map = {
      ctx.aspect_key('dbt-node'): aspects.node_aspect(
          ctx, unique_id, sq, 'saved_query'
      ),
      ctx.aspect_key('dbt-saved-query'): aspects.make_aspect(
          ctx.aspect_fqn('dbt-saved-query'),
          {
              'queryMetrics': qp.get('metrics') or [],
              'groupBy': qp.get('group_by') or [],
              'whereClause': _where_clause(qp.get('where')),
              'exports': exports,
              'metadata': _json_or_empty(sq.get('metadata')),
          },
      ),
  }
  project_name = sq.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = sq.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-saved-query', project_name, resource_name)
  return _entry(ctx, unique_id, 'dbt-saved-query', aspects_map, fqn)


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

  dq = {
      'columnName': (
          test_node.get('column_name') or kwargs.get('column_name') or ''
      ),
      'sqlDefinition': (
          test_node.get('compiled_code') or test_node.get('compiled_sql') or ''
      ),
      'severity': config.get('severity') or '',
      'storeFailures': bool(config.get('store_failures', False)),
      'status': res.get('status') or '',
      'testCategory': _test_category(test_node),
      'message': res.get('message') or '',
  }
  failures = res.get('failures')
  if isinstance(failures, int):
    dq['failures'] = failures
  rows_affected = (res.get('adapter_response') or {}).get('rows_affected')
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
  project_name = test_node.get('package_name') or _DEFAULT_PROJECT_NAME
  resource_name = test_node.get('name') or ''
  fqn = ctx.dbt_resource_fqn('dbt-test', project_name, resource_name)
  return _entry(ctx, unique_id, 'dbt-test', aspects_map, fqn)


def _check_size_limits(unique_id: str, record: dict[str, Any]) -> None:
  """Fails the transform when an entry or aspect exceeds a Dataplex size limit.

  dbt resources carry arbitrary user content (compiled test SQL, macro bodies,
  very wide schemas, free-form ``meta`` blobs), so a single aspect or a whole
  entry can outgrow the sizes the import job accepts. The import job would
  reject such an item server-side, so we fail here -- before the file is copied
  to GCS and an import job is started -- and point at the offending resource.
  See https://cloud.google.com/dataplex/docs/quotas#limits.

  Args:
    unique_id: the dbt unique_id of the resource, for the error message.
    record: the entry record built for the resource.

  Raises:
    naming.TransformError: if an aspect exceeds the per-aspect limit or the
      whole entry exceeds the per-entry limit.
  """
  entry = record['entry']
  for key, aspect in entry['aspects'].items():
    aspect_bytes = len(json.dumps(aspect.get('data', {})).encode('utf-8'))
    if aspect_bytes > naming.MAX_ASPECT_JSON_BYTES:
      raise naming.TransformError(
          'Aspect [{0}] on dbt resource [{1}] is {2} KB, over the {3} KB '
          'per-aspect limit, and would be rejected by the import job. Reduce '
          "the resource's content (e.g. compiled SQL, macro body, schema) and "
          're-run.'.format(
              key,
              unique_id,
              aspect_bytes // 1024,
              naming.MAX_ASPECT_JSON_BYTES // 1024,
          )
      )
  entry_bytes = len(json.dumps(entry).encode('utf-8'))
  if entry_bytes > naming.MAX_ENTRY_BYTES:
    raise naming.TransformError(
        'dbt resource [{0}] builds a {1} KB entry, over the {2} KB entry size '
        'limit, and would be rejected by the import job. Reduce the '
        "resource's content and re-run.".format(
            unique_id, entry_bytes // 1024, naming.MAX_ENTRY_BYTES // 1024
        )
    )


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
  group_map = manifest.get('group_map') or {}
  run_results_map = _index_by_unique_id((run_results or {}).get('results'))
  sources_map = _index_by_unique_id((sources or {}).get('results'))

  entries = []
  # entry_id -> unique_id, tracked as entries are added. This hands entry_links
  # a ready id set and lets us warn when the lossy unique_id -> entry_id mapping
  # (naming.entry_id lowercases and replaces dots) collapses two distinct
  # resources onto one id -- one would silently overwrite the other on import.
  ids = {}

  def add(unique_id: str, record: dict[str, Any]) -> None:
    entries.append(record)
    entry_id = naming.entry_id(unique_id)
    if len(entry_id) > naming.MAX_ENTRY_ID_LENGTH:
      log.warning(
          'Dataplex entry id [{0}] for dbt resource [{1}] exceeds the '
          '{2}-character limit and will be rejected on import.'.format(
              entry_id, unique_id, naming.MAX_ENTRY_ID_LENGTH
          )
      )
    _check_size_limits(unique_id, record)
    if entry_id in ids and ids[entry_id] != unique_id:
      log.warning(
          'Two dbt resources map to the same Dataplex entry id [{0}] ([{1}] '
          'and [{2}]); one will overwrite the other on import.'.format(
              entry_id, ids[entry_id], unique_id
          )
      )
    ids[entry_id] = unique_id

  add(_project_unique_id(manifest), _build_project_entry(ctx, manifest))

  for unique_id, node in nodes.items():
    rt = node.get('resource_type')
    if rt == 'model':
      add(unique_id, _build_model_entry(ctx, unique_id, node, catalog_nodes))
    elif rt == 'seed':
      add(unique_id, _build_seed_entry(ctx, unique_id, node, catalog_nodes))
    elif rt == 'snapshot':
      add(unique_id, _build_snapshot_entry(ctx, unique_id, node))
    elif rt == 'test':
      add(unique_id, _build_test_entry(ctx, unique_id, node, run_results_map))

  for unique_id, src in manifest_sources.items():
    add(unique_id, _build_source_entry(ctx, unique_id, src, sources_map))

  for unique_id, group in (manifest.get('groups') or {}).items():
    add(unique_id, _build_group_entry(ctx, unique_id, group, group_map))

  for unique_id, exposure in (manifest.get('exposures') or {}).items():
    add(unique_id, _build_exposure_entry(ctx, unique_id, exposure))

  for unique_id, metric in (manifest.get('metrics') or {}).items():
    add(unique_id, _build_metric_entry(ctx, unique_id, metric))

  for unique_id, macro in (manifest.get('macros') or {}).items():
    # Only emit macros defined in the user's project (not imported packages).
    if macro.get('package_name') != project_name:
      continue
    add(unique_id, _build_macro_entry(ctx, unique_id, macro))

  for unique_id, sm in (manifest.get('semantic_models') or {}).items():
    add(unique_id, _build_semantic_model_entry(ctx, unique_id, sm))

  for unique_id, sq in (manifest.get('saved_queries') or {}).items():
    add(unique_id, _build_saved_query_entry(ctx, unique_id, sq))

  return entries, set(ids)
