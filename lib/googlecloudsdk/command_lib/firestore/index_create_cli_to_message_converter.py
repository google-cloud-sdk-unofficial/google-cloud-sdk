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
"""CLI to message converter utilities for Firestore index create commands."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.firestore import api_utils as fs_api_utils


def _KebabToCamel(s):
  """Converts a kebab-case string to camelCase."""
  parts = s.split('-')
  return parts[0] + ''.join(p.title() for p in parts[1:])


def _KebabToCamelKeysDict(d):
  """Recursively converts dict keys to camelCase."""
  if isinstance(d, dict):
    return {
        _KebabToCamel(k): _KebabToCamelKeysDict(v)
        for k, v in d.items()
        if v is not None
    }

  if isinstance(d, list):
    return [_KebabToCamelKeysDict(v) for v in d if v is not None]

  return d


def _NormalizeEnum(s):
  return s.upper().replace('-', '_') if s else None


def BuildIndexMessage(
    field_configs,
    query_scope,
    api_scope,
    multikey,
    density,
    unique,
    search_index_options,
):
  """Builds a GoogleFirestoreAdminV1Index message from parsed arguments."""
  messages = fs_api_utils.GetMessages()

  # Coerece keys to match proto casing.
  fields = _KebabToCamelKeysDict(field_configs)

  # Coerce top level enums to match proto enum casing. Nested enums are
  # normalized during parsing.
  index_dict = {
      'queryScope': _NormalizeEnum(query_scope),
      'apiScope': _NormalizeEnum(api_scope),
      'density': _NormalizeEnum(density),
      'multikey': multikey,
      'unique': unique,
      'searchIndexOptions': _KebabToCamelKeysDict(search_index_options),
      'fields': fields,
  }

  clean_dict = _KebabToCamelKeysDict(index_dict)
  return encoding.DictToMessage(
      clean_dict, messages.GoogleFirestoreAdminV1Index
  )
