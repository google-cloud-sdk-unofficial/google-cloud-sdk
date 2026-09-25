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
"""Utility functions for BigQuery translation commands."""

import functools
import json
import pkgutil

from googlecloudsdk.core import exceptions


@functools.cache
def _get_dialect_registry():
  """Gets dialect registry: input_dialects, output_dialects, dialect_pairs.

  The mapping is loaded from a JSON resource file.

  Returns:
    A dict with dialect registry.

  Raises:
    exceptions.Error: If the dialect registry fails to load.
  """
  try:
    data = pkgutil.get_data(
        'surface.bq.translation', 'dialect_registry.json'
    )
    if data is None:
      raise exceptions.Error(
          'Could not read dialect_registry.json from package data.'
      )
    registry = json.loads(data.decode('utf-8'))
    return registry
  except Exception as e:
    raise exceptions.Error(f'Failed to load dialect registry: {e}')


def get_task_type(source_dialect: str, target_dialect: str) -> str:
  """Returns the translation task type based on the source dialect."""
  registry = _get_dialect_registry()
  source_dialect_map = {}
  for dialect in registry.get('input_dialects', []):
    legacy_name = dialect.get('legacy_batch_name')
    name = dialect.get('name')
    if legacy_name:
      if name:
        source_dialect_map[name.lower()] = legacy_name
      source_dialect_map[legacy_name.lower()] = legacy_name
    elif name:
      source_dialect_map[name.lower()] = name
  source_legacy_batch_name = source_dialect_map.get(
      source_dialect.lower(), source_dialect
  )
  target_dialect_map = {}
  for dialect in registry.get('output_dialects', []):
    legacy_name = dialect.get('legacy_batch_name')
    name = dialect.get('name')
    if legacy_name:
      if name:
        target_dialect_map[name.lower()] = legacy_name
      target_dialect_map[legacy_name.lower()] = legacy_name
    elif name:
      target_dialect_map[name.lower()] = name
  target_legacy_batch_name = target_dialect_map.get(
      target_dialect.lower(), target_dialect
  )
  task_type = (
      f'{source_legacy_batch_name}2{target_legacy_batch_name}_Translation'
  )
  valid_task_type = False
  for pair in registry['dialect_pairs']:
    if task_type in pair.get('legacy_batch_name', []):
      valid_task_type = True
      break
  if not valid_task_type:
    raise exceptions.Error(
        f'Translation from {source_dialect} to {target_dialect} is not'
        ' supported.'
    )
  return task_type
