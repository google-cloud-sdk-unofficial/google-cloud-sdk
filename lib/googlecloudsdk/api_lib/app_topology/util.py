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
"""Utilities for App Topology API."""

from apitools.base.py import encoding
from apitools.base.py import extra_types
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base

VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1',
    base.ReleaseTrack.BETA: 'v1',
    base.ReleaseTrack.GA: 'v1',
}


def GetMessagesModule(release_track=base.ReleaseTrack.ALPHA):
  """Returns the Apitools messages module for the specified release track.

  Args:
    release_track: base.ReleaseTrack or str, The release track (ALPHA, BETA, GA)
      or an explicit version string (e.g. 'v1').

  Returns:
    module: The generated Apitools messages module for App Topology.
  """
  if isinstance(release_track, str):
    api_version = release_track
  else:
    api_version = VERSION_MAP.get(release_track, 'v1')
  return apis.GetMessagesModule('apptopology', api_version)


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA, no_http=False):
  """Returns the Apitools client instance for the specified release track.

  Args:
    release_track: base.ReleaseTrack or str, The release track (ALPHA, BETA, GA)
      or an explicit version string (e.g. 'v1').
    no_http: bool, If True, creates a client instance without initializing the
      HTTP transport (used primarily in hermetic unit test mocking).

  Returns:
    apitools.base.py.BaseApiClient: The initialized App Topology client
    instance.
  """
  if isinstance(release_track, str):
    api_version = release_track
  else:
    api_version = VERSION_MAP.get(release_track, 'v1')
  return apis.GetClientInstance('apptopology', api_version, no_http=no_http)


def _UnpackExtraTypeValue(val):
  """Recursively unpacks extra_types into standard Python primitives.

  In Apitools Protobuf definitions, map and open JSON fields (such as
  Node.properties
  and Edge.properties) are represented as `extra_types.JsonValue` objects or
  `additionalProperties` key-value message arrays. This helper traverses the
  structure
  and converts them into clean Python dictionaries, lists, strings, and numbers.

  Args:
    val: Any, The value to unpack.

  Returns:
    The unpacked primitive value (dict, list, str, int, float, bool, or None).
  """
  if val is None:
    return None
  # Unpack explicit Apitools JSON types.
  if isinstance(
      val,
      (extra_types.JsonValue, extra_types.JsonObject, extra_types.JsonArray),
  ):
    return _UnpackExtraTypeValue(encoding.MessageToPyValue(val))
  # Unpack protobuf objects with additionalProperties attribute.
  if hasattr(val, 'additionalProperties'):
    result = {}
    for prop in val.additionalProperties:
      result[prop.key] = _UnpackExtraTypeValue(prop.value)
    return result
  # Traverse lists.
  if isinstance(val, list):
    return [_UnpackExtraTypeValue(item) for item in val]
  # Flatten dictionary representations of additionalProperties lists.
  if isinstance(val, dict):
    if 'additionalProperties' in val and isinstance(
        val['additionalProperties'], list
    ):
      return {
          prop['key']: _UnpackExtraTypeValue(prop.get('value'))
          for prop in val['additionalProperties']
          if isinstance(prop, dict) and 'key' in prop
      }
    # Unpack array_value dictionary representations.
    if 'array_value' in val and isinstance(val['array_value'], dict):
      entries = val['array_value'].get('entries', [])
      return [_UnpackExtraTypeValue(item) for item in entries]
    if 'array_value' in val and isinstance(val['array_value'], list):
      return [_UnpackExtraTypeValue(item) for item in val['array_value']]
    # Unpack object_value dictionary representations.
    if 'object_value' in val and isinstance(val['object_value'], dict):
      props = val['object_value'].get(
          'properties', val['object_value'].get('additionalProperties', [])
      )
      if isinstance(props, list):
        return {
            prop['key']: _UnpackExtraTypeValue(prop.get('value'))
            for prop in props
            if isinstance(prop, dict) and 'key' in prop
        }
      return {
          k: _UnpackExtraTypeValue(v) for k, v in val['object_value'].items()
      }
    # Unpack scalar dictionary representations of extra_types.JsonValue.
    for key in (
        'string_value',
        'integer_value',
        'double_value',
        'boolean_value',
    ):
      if key in val and len(val) == 1:
        return val[key]
    if 'is_null' in val and val['is_null'] and len(val) == 1:
      return None
    return {k: _UnpackExtraTypeValue(v) for k, v in val.items()}
  return val


def NormalizeGraphProperties(graph):
  """Unpacks apitools additionalProperties in Node and Edge properties.

  Takes an API response `Graph` message or dictionary and returns a normalized
  dictionary representation where all nested node and edge properties are
  flattened
  into intuitive key-value pairs suitable for YAML/JSON display.

  Args:
    graph: Graph protobuf message returned from API, or dict.

  Returns:
    dict or None: The normalized graph dictionary representation, or None if
    graph is None.
  """
  if not graph:
    return graph

  graph_dict = (
      graph if isinstance(graph, dict) else encoding.MessageToPyValue(graph)
  )
  # Normalize node properties.
  if 'nodes' in graph_dict and isinstance(graph_dict['nodes'], list):
    for node in graph_dict['nodes']:
      if isinstance(node, dict) and 'properties' in node:
        node['properties'] = _UnpackExtraTypeValue(node['properties'])

  # Normalize edge properties.
  if 'edges' in graph_dict and isinstance(graph_dict['edges'], list):
    for edge in graph_dict['edges']:
      if isinstance(edge, dict) and 'properties' in edge:
        edge['properties'] = _UnpackExtraTypeValue(edge['properties'])

  return graph_dict
