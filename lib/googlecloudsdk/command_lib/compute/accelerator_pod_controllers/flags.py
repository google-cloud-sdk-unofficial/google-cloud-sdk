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
"""Flags and request modification hooks for accelerator-pod-controllers commands."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import yaml
import six

VALID_INTERFACE_KEYS = frozenset({
    'key',
    'type',
    'network',
    'subnetwork',
    'ipv4_address',
    'ipv4address',
    'ipv4',
    'ipv6_address',
    'ipv6address',
    'ipv6',
    'trust_config',
    'trustconfig',
})


def _normalize_dict(raw_dict):
  """Normalizes dictionary keys by replacing hyphens with underscores and lowercasing."""
  normalized = {}
  for k, v in raw_dict.items():
    norm_k = k.replace('-', '_').lower()
    normalized[norm_k] = v
  return normalized


def _lookup_enum_value(enum_cls, name):
  """Looks up an enum value by name, returning None if not found."""
  try:
    return enum_cls.lookup_by_name(name)
  except KeyError:
    return None


def _parse_type_enum(messages, raw_type, source_label='--management-interface'):
  """Parses a string into ManagementInterface.TypeValueValuesEnum."""
  if not raw_type:
    raise exceptions.InvalidArgumentException(
        source_label, 'Management interface must specify a "type".'
    )
  enum_cls = messages.ManagementInterface.TypeValueValuesEnum

  # Direct lookup
  val = _lookup_enum_value(enum_cls, raw_type)
  if val is not None:
    return val
  # Uppercase + underscores
  normalized = raw_type.upper().replace('-', '_')
  val = _lookup_enum_value(enum_cls, normalized)
  if val is not None:
    return val
  # Prefix with TYPE_ if not present
  if not normalized.startswith('TYPE_'):
    val = _lookup_enum_value(enum_cls, 'TYPE_' + normalized)
    if val is not None:
      return val
  raise exceptions.InvalidArgumentException(
      source_label,
      'Invalid type [{}]. Valid choices include:'
      ' TYPE_NVLINK_PARTITION_MANAGEMENT, TYPE_NVLINK_SWITCH_MONITORING,'
      ' TYPE_UNSPECIFIED.'.format(raw_type),
  )


def _parse_interface_dict(
    messages, raw_dict, source_label='--management-interface'
):
  """Parses an interface dict into (key, ManagementInterface message)."""
  normalized_dict = _normalize_dict(raw_dict)
  for k in sorted(normalized_dict.keys()):
    if k not in VALID_INTERFACE_KEYS:
      raise exceptions.InvalidArgumentException(
          source_label,
          'Unknown key [{}] specified in management interface.'.format(k),
      )
  key = normalized_dict.get('key')
  if not key:
    raise exceptions.InvalidArgumentException(
        source_label, 'Each management interface must specify a "key".'
    )

  type_enum = _parse_type_enum(
      messages, normalized_dict.get('type'), source_label
  )
  network = normalized_dict.get('network')
  subnetwork = normalized_dict.get('subnetwork')
  ipv4_address = (
      normalized_dict.get('ipv4_address')
      or normalized_dict.get('ipv4address')
      or normalized_dict.get('ipv4')
  )
  ipv6_address = (
      normalized_dict.get('ipv6_address')
      or normalized_dict.get('ipv6address')
      or normalized_dict.get('ipv6')
  )
  trust_config = normalized_dict.get('trust_config') or normalized_dict.get(
      'trustconfig'
  )

  auth_config = None
  if trust_config:
    auth_config = messages.AuthenticationConfig(trustConfig=trust_config)

  interface_msg = messages.ManagementInterface(
      type=type_enum,
      network=network,
      subnetwork=subnetwork,
      ipv4Address=ipv4_address,
      ipv6Address=ipv6_address,
      authenticationConfig=auth_config,
  )
  return key, interface_msg


def _parse_interfaces_file(messages, file_path):
  """Parses a YAML/JSON file into a dict of {key: ManagementInterface}."""
  try:
    content = yaml.load_path(file_path)
  except (yaml.FileLoadError, yaml.YAMLParseError) as e:
    raise exceptions.BadFileException(
        'Could not load management interfaces file [{}]: {}'.format(
            file_path, six.text_type(e)
        )
    )

  if not isinstance(content, (dict, list)):
    raise exceptions.BadFileException(
        'File [{}] must contain a YAML/JSON mapping or list of management'
        ' interfaces.'.format(file_path)
    )

  interfaces = {}
  source_label = '--management-interfaces-file [{}]'.format(file_path)

  if isinstance(content, dict):
    for k, v in content.items():
      if not isinstance(v, dict):
        raise exceptions.BadFileException(
            'Management interface entry [{}] in [{}] must be a mapping.'.format(
                k, file_path
            )
        )
      entry = dict(v)
      entry.setdefault('key', k)
      parsed_key, parsed_msg = _parse_interface_dict(
          messages, entry, source_label
      )
      interfaces[parsed_key] = parsed_msg
  else:
    for idx, item in enumerate(content):
      if not isinstance(item, dict):
        raise exceptions.BadFileException(
            'Management interface item #{} in [{}] must be a mapping.'.format(
                idx, file_path
            )
        )
      parsed_key, parsed_msg = _parse_interface_dict(
          messages, item, source_label
      )
      if parsed_key in interfaces:
        raise exceptions.BadFileException(
            'Duplicate management interface key [{}] in [{}].'.format(
                parsed_key, file_path
            )
        )
      interfaces[parsed_key] = parsed_msg

  return interfaces


def modify_create_request(resource_ref, args, request_msg):
  """Modify the create request with resource name and management interfaces."""
  messages = apis.GetMessagesModule('compute', 'alpha')

  if request_msg.acceleratorPodController is None:
    request_msg.acceleratorPodController = messages.AcceleratorPodController()

  # Set resource name in body
  request_msg.acceleratorPodController.name = resource_ref.Name()

  # Collect all management interfaces
  all_interfaces = {}

  file_arg = args.management_interfaces_file
  if file_arg:
    file_interfaces = _parse_interfaces_file(messages, file_arg)
    all_interfaces.update(file_interfaces)

  mgmt_interfaces_arg = args.management_interface
  if mgmt_interfaces_arg:
    items = (
        mgmt_interfaces_arg
        if isinstance(mgmt_interfaces_arg, list)
        else [mgmt_interfaces_arg]
    )
    for item in items:
      k, v = _parse_interface_dict(
          messages, item, source_label='--management-interface'
      )
      if k in all_interfaces:
        raise exceptions.InvalidArgumentException(
            '--management-interface',
            'Duplicate management interface key [{}] specified.'.format(k),
        )
      all_interfaces[k] = v

  if all_interfaces:
    additional_props = [
        messages.AcceleratorPodController.ManagementInterfacesValue.AdditionalProperty(
            key=k, value=v
        )
        for k, v in sorted(all_interfaces.items())
    ]
    request_msg.acceleratorPodController.managementInterfaces = (
        messages.AcceleratorPodController.ManagementInterfacesValue(
            additionalProperties=additional_props
        )
    )

  return request_msg
