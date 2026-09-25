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
"""Utility functions for Resource Manager CapabilityConfigs commands."""

from googlecloudsdk.calliope import exceptions as calliope_exceptions


def ParseTypes(types_list, messages):
  """Parses a list of string type names into CapabilityConfig.TypesValueListEntryValuesEnum values."""
  if types_list is None:
    return []

  type_enum = messages.CapabilityConfig.TypesValueListEntryValuesEnum
  type_map = {
      'app-management': type_enum.APP_MANAGEMENT,
      'agent-management': type_enum.AGENT_MANAGEMENT,
      'APP_MANAGEMENT': type_enum.APP_MANAGEMENT,
      'AGENT_MANAGEMENT': type_enum.AGENT_MANAGEMENT,
  }

  result = []
  for t in types_list:
    if t in type_map:
      result.append(type_map[t])
    else:
      raise calliope_exceptions.InvalidArgumentException(
          '--types', f'Unrecognized CapabilityConfig type [{t}].'
      )
  return result


def GetUpdateMask(args):
  """Generates a FieldMask string for the update command."""
  mask_fields = []
  if args.IsSpecified('display_name'):
    mask_fields.append('display_name')
  if args.IsSpecified('types'):
    mask_fields.append('types')
  if args.IsSpecified('boundaries') or args.IsSpecified('clear_boundaries'):
    mask_fields.append('boundaries')
  return ','.join(mask_fields)
