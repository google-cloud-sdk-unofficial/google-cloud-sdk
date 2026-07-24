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


def stat_int(stats: dict[str, Any], key: str) -> int | None:
  """Returns a catalog stat as int, or None if absent / not included.

  dbt reports stat values as strings and sometimes as decimals (e.g. "2048.0"),
  so parse via float before truncating to int.

  Args:
    stats: the catalog node's ``stats`` mapping.
    key: the stat name to read (e.g. 'row_count', 'bytes').

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


def schema_aspect_from_columns(
    ctx: naming.Context,
    columns: dict[str, Any],
    type_key: str,
    desc_key: str,
) -> dict[str, Any]:
  """Builds the dbt-schema aspect from a dbt/catalog columns mapping.

  Args:
    ctx: the naming.Context holding the naming coordinates for this run.
    columns: the dbt/catalog ``columns`` mapping (column name -> column dict).
    type_key: the per-column key holding the data type ('type' or 'data_type').
    desc_key: the per-column key holding the description ('comment' or
      'description').

  Returns:
    A dbt-schema aspect record.
  """
  fields = [
      {
          'columnId': col_name,
          'name': col_data.get('name', col_name),
          'dataType': col_data.get(type_key) or '',
          'description': col_data.get(desc_key) or '',
      }
      for col_name, col_data in columns.items()
  ]
  return make_aspect(ctx.aspect_fqn('dbt-schema'), {'columns': fields})
