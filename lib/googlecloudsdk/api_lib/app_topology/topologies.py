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
"""Discovered Resources Topology client for App Topology API."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.app_topology import GetClientInstance
from googlecloudsdk.api_lib.app_topology import GetMessagesModule
from googlecloudsdk.api_lib.app_topology import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io


def _SnakeToCamel(key):
  """Converts snake_case, kebab-case, SCREAMING_SNAKE_CASE to lowerCamelCase.

  This normalization ensures that user-provided YAML or JSON pattern keys
  (e.g., `starting_node`, `starting-node`, `STARTING_NODE`, or `StartingNode`)
  map deterministically to Apitools protobuf message fields (`startingNode`).

  Args:
    key: str or Any, The dictionary key to normalize.

  Returns:
    str: The normalized lowerCamelCase key.
  """
  if not key:
    return key
  key_str = str(key)
  # Handle snake_case, kebab-case, and multi-word SCREAMING_SNAKE_CASE
  # (e.g. 'label_properties_pattern', 'label-matcher-expr', 'STARTING_NODE').
  if '_' in key_str or '-' in key_str:
    normalized_key = key_str.replace('-', '_')
    parts = [p for p in normalized_key.split('_') if p]
    if not parts:
      return key_str
    return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])
  # Handle single-word all-caps keys (e.g. 'EDGE' -> 'edge').
  if key_str.isupper():
    return key_str.lower()
  # Handle standard UpperCamelCase keys (e.g. 'StartingNode' -> 'startingNode').
  return key_str[0].lower() + key_str[1:]


def _NormalizeValue(key, val):
  """Normalizes dictionary values, specifically protobuf enum strings.

  Apitools Protobuf Enum fields (such as DirectionValueValuesEnum in
  EdgePattern)
  require uppercase underscore-separated names (e.g. 'TO',
  'DIRECTION_UNSPECIFIED').
  This function strips whitespace, handles kebab-case, and converts enum string
  literals to uppercase before serialization.

  Args:
    key: str, The parent key identifying the field.
    val: Any, The value associated with the key.

  Returns:
    Any: The normalized value or recursively normalized nested structure.
  """
  if str(key).lower() in ('direction',) and isinstance(val, str):
    # Enum normalization: handles " to " -> "DIRECTION_UNSPECIFIED"
    return val.strip().upper().replace('-', '_')
  return _NormalizeData(val)


def _NormalizeData(data):
  """Normalizes dictionary keys and values for Protobuf serialization.

  Walks through nested dictionaries and lists to ensure all keys conform to
  lowerCamelCase and enum string values are properly cased.

  Args:
    data: dict, list, or primitive, The data structure to normalize.

  Returns:
    The normalized data structure.
  """
  if isinstance(data, dict):
    return {_SnakeToCamel(k): _NormalizeValue(k, v) for k, v in data.items()}
  if isinstance(data, list):
    return [_NormalizeData(item) for item in data]
  return data


class DiscoveredResourcesTopologiesClient(object):
  """Client for Discovered Resources Topology in App Topology API."""

  def __init__(self, version='v1'):
    self.client = GetClientInstance(version)
    self.messages = GetMessagesModule(version)
    self._service = self.client.projects_locations_discoveredResourcesTopology

  def _ParseFilter(self, pattern=None, pattern_file=None):
    """Parses an inline pattern string or file into a GraphPattern message.

    Supports reading YAML/JSON filter definitions from inline CLI arguments,
    local filesystem files, or standard input (`-`). Normalizes user inputs
    into strongly typed Apitools GraphPattern messages.

    Args:
      pattern: str or None, Inline YAML or JSON string.
      pattern_file: str or None, Path to a YAML/JSON file or '-' for stdin.

    Returns:
      messages.GraphPattern or None: Deserialized GraphPattern protobuf message,
        or None if no filter was specified or the filter file was
        empty/comment-only.

    Raises:
      exceptions.Error: If the pattern file cannot be read, contains invalid
      syntax,
        or is not a YAML dictionary/object.
    """
    if pattern is None and pattern_file is None:
      return None

    # Read pattern content from file/stdin or use inline string.
    if pattern_file:
      try:
        content = console_io.ReadFromFileOrStdin(pattern_file, binary=False)
      except Exception as e:
        raise exceptions.Error(
            f'Failed to read pattern file [{pattern_file}]: {e}'
        )
    else:
      content = pattern

    # Handle empty string inputs (e.g. --pattern="").
    if not content or not content.strip():
      return None

    try:
      parsed_dict = yaml.load(content)
      # Handle empty or comment-only YAML documents (e.g. '# comments').
      if parsed_dict is None:
        return None
      if not isinstance(parsed_dict, dict):
        raise exceptions.Error(
            'Invalid filter format: Expected YAML/JSON object for GraphPattern.'
        )
      # Recursively normalize key casings and enum values.
      normalized_dict = _NormalizeData(parsed_dict)
      return encoding.PyValueToMessage(
          self.messages.GraphPattern, normalized_dict
      )
    except Exception as e:
      if isinstance(e, exceptions.Error):
        raise
      raise exceptions.Error(f'Failed to parse GraphPattern filter: {e}')

  def Generate(self, name, domains, pattern=None, pattern_file=None):
    """Generates discovered resources topology graph across specified domains.

    Args:
      name: str, Fully qualified resource name of discoveredResourcesTopology
        (e.g.,
        'projects/{project}/locations/{location}/discoveredResourcesTopology').
      domains: list[str], Fully qualified topology domain resource names (e.g.,
        ['projects/{p}/locations/{l}/domains/{d}']).
      pattern: str or None, Inline YAML/JSON filter pattern.
      pattern_file: str or None, Path to pattern file or '-' for stdin.

    Returns:
      dict: Normalized graph dictionary with unpacked node and edge properties.
    """
    filter_msg = self._ParseFilter(pattern=pattern, pattern_file=pattern_file)
    body = self.messages.GenerateDiscoveredResourcesTopologyRequest(
        topologyDomains=domains, filter=filter_msg
    )
    req_class = getattr(
        self.messages,
        'ApptopologyProjectsLocationsDiscovered'
        'ResourcesTopologyGenerateRequest',
    )
    request = req_class(
        name=name, generateDiscoveredResourcesTopologyRequest=body
    )
    response = self._service.Generate(request)
    return util.NormalizeGraphProperties(response.graph)
