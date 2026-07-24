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

One entry is emitted per dbt resource of interest (project, model). Every entry
carries the universal ``dbt-node`` aspect plus its resource-specific aspect;
models additionally carry the optional ``dbt-schema`` aspect. All aspect field
names follow the canonical types verbatim (camelCase).
"""

from __future__ import annotations

from typing import Any

from googlecloudsdk.command_lib.dataplex.dbt import aspects
from googlecloudsdk.command_lib.dataplex.dbt import naming
from googlecloudsdk.core import log

# Fallback dbt project name when the manifest metadata omits ``project_name``.
_DEFAULT_PROJECT_NAME = 'dbt_project'


def _entry(
    ctx: naming.Context,
    unique_id: str,
    entry_type: str,
    aspects_map: dict[str, Any],
) -> dict[str, Any]:
  """Wraps an aspect map in the entry record shared by every builder."""
  return {
      'entry': {
          'name': ctx.entry_name(naming.entry_id(unique_id)),
          'entryType': ctx.entry_type(entry_type),
          'aspects': aspects_map,
      }
  }


def _project_unique_id(manifest: dict[str, Any]) -> str:
  """The dbt unique_id of the synthetic project entry."""
  project_name = (
      manifest.get('metadata', {}).get('project_name') or _DEFAULT_PROJECT_NAME
  )
  return 'project.{0}'.format(project_name)


def _build_project_entry(
    ctx: naming.Context, manifest: dict[str, Any]
) -> dict[str, Any]:
  """Builds the dbt-project entry from the manifest metadata."""
  meta = manifest.get('metadata', {})
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
  return _entry(ctx, _project_unique_id(manifest), 'dbt-project', aspects_map)


def _model_contracts_aspect(
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
    column_contracts.append({
        'name': col.get('name', col_name),
        'dataType': col.get('data_type') or '',
        'constraints': [
            c.get('type', '')
            for c in col.get('constraints') or []
            if c.get('type')
        ],
    })
  return aspects.make_aspect(
      ctx.aspect_fqn('dbt-model-contracts'),
      {
          'contractEnforced': enforced,
          'modelConstraints': model_constraints,
          'columnContracts': column_contracts,
      },
  )


def _build_model_entry(
    ctx: naming.Context,
    unique_id: str,
    node: dict[str, Any],
    catalog_nodes: dict[str, Any],
) -> dict[str, Any]:
  """Builds a dbt-model entry with node, model, schema and contract aspects."""
  config = node.get('config', {})
  cat_node = catalog_nodes.get(unique_id, {})
  stats = cat_node.get('stats', {})
  enforced = bool((node.get('contract') or {}).get('enforced', False))

  model_data = {
      'isContractEnforced': enforced,
      'materializationType': config.get('materialized') or '',
  }
  aspects.add_stat(model_data, 'rowCount', stats, 'row_count')
  aspects.add_stat(model_data, 'byteCount', stats, 'bytes')

  aspects_map = {
      ctx.aspect_key('dbt-node'): aspects.node_aspect(
          ctx, unique_id, node, 'model'
      ),
      ctx.aspect_key('dbt-model'): aspects.make_aspect(
          ctx.aspect_fqn('dbt-model'), model_data
      ),
  }

  columns = cat_node.get('columns', {})
  if columns:
    aspects_map[ctx.aspect_key('dbt-schema')] = (
        aspects.schema_aspect_from_columns(ctx, columns, 'type', 'comment')
    )

  contracts = _model_contracts_aspect(ctx, node, enforced)
  if contracts:
    aspects_map[ctx.aspect_key('dbt-model-contracts')] = contracts

  return _entry(ctx, unique_id, 'dbt-model', aspects_map)


def build_entries(
    ctx: naming.Context, manifest: dict[str, Any], catalog: dict[str, Any]
) -> tuple[list[dict[str, Any]], set[str]]:
  """Builds every dbt entry record from the parsed artifacts.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    manifest: the parsed dbt manifest.json.
    catalog: the parsed dbt catalog.json (or {} when absent).

  Returns:
    (entries, known_ids): the entry records, and the set of Dataplex entry ids
    they occupy. entry_links consumes the id set directly instead of parsing
    ids back out of the entry resource names.
  """
  nodes = manifest.get('nodes', {})
  catalog_nodes = catalog.get('nodes', {})

  entries = []
  # entry_id -> unique_id, tracked as entries are added. This hands entry_links
  # a ready id set and lets us warn when the lossy unique_id -> entry_id mapping
  # (naming.entry_id lowercases and replaces dots) collapses two distinct
  # resources onto one id -- one would silently overwrite the other on import.
  ids = {}

  def add(unique_id: str, record: dict[str, Any]) -> None:
    entries.append(record)
    entry_id = naming.entry_id(unique_id)
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

  return entries, set(ids)
