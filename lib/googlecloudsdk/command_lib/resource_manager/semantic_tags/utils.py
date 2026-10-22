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
"""Utilities for Resource Manager Semantic Tags commands."""

import re
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import resource_expr_rewrite

CATALOG_PARENT = 'projects/gcp-semantic-tags-catalog'
CATALOG_PARENT_QUAL = 'projects/gcp-semantic-tags-catalog-qual'
CATALOG_PARENT_TEST = 'projects/gcp-semantic-tags-catalog-test'

_PARENT_PATTERN = re.compile(r'^(organizations|projects)/([^/]+)$')
_VALUE_NAME_PATTERN = re.compile(
    r'^(organizations|projects)/([^/]+)/locations/([^/]+)/semanticTagValues/([^/]+)$'
)
_VALUE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,63}$')
_FULL_KEY_NAME_PATTERN = re.compile(
    r'^(organizations|projects)/([^/]+)/locations/([^/]+)/semanticTagKeys/([^/]+)$'
)
_BINDING_NAME_PATTERN = re.compile(
    r'^(organizations|projects)/([^/]+)/locations/([^/]+)/semanticTagBindings/([^/]+)$'
)


def GetCatalogParent() -> str:
  """Returns the environment-dependent GCP catalog project parent."""
  endpoint = (
      properties.VALUES.api_endpoint_overrides.cloudresourcemanager.Get() or ''
  ).lower()
  if 'stagqual-' in endpoint or 'staging-' in endpoint:
    return CATALOG_PARENT_QUAL
  if 'autopush-' in endpoint or 'test-' in endpoint or '.sandbox.' in endpoint:
    return CATALOG_PARENT_TEST
  return CATALOG_PARENT


def ValidateParent(parent: str) -> str:
  """Validates that parent is in the form organizations/{id} or projects/{id}."""
  if not _PARENT_PATTERN.match(parent):
    raise calliope_exceptions.InvalidArgumentException(
        '--parent',
        f'Invalid parent [{parent}]. Must be in the format'
        ' organizations/{organization_id} or projects/{project_id}.',
    )
  return parent


def GetParent(args, default_to_catalog: bool = False) -> str:
  """Resolves the parent container from --parent or defaults."""
  if args.IsSpecified('parent') and args.parent:
    return ValidateParent(args.parent)
  if default_to_catalog:
    return GetCatalogParent()
  project = properties.VALUES.core.project.Get()
  if not project:
    raise calliope_exceptions.RequiredArgumentException(
        '--parent',
        'Either --parent or the [core/project] property must be specified.',
    )
  return f'projects/{project}'


def NormalizeSemanticTagKey(key: str, location: str = 'global') -> str:
  """Normalizes a SemanticTagKey reference into a full resource name.

  Args:
    key: The key reference (full URI, `locations/{loc}/semanticTagKeys/{id}`,
      `semanticTagKeys/{id}`, or short key ID `{id}`).
    location: Location to use when expanding a shorthand key reference.

  Returns:
    The full SemanticTagKey resource name.
  """
  if not key:
    raise calliope_exceptions.InvalidArgumentException(
        '--key', 'Key cannot be empty.'
    )
  catalog_parent = GetCatalogParent()
  if _FULL_KEY_NAME_PATTERN.match(key):
    return key
  if key.startswith('locations/'):
    full_key = f'{catalog_parent}/{key}'
    if _FULL_KEY_NAME_PATTERN.match(full_key):
      return full_key
  if key.startswith('semanticTagKeys/'):
    key_id = key.removeprefix('semanticTagKeys/')
    if key_id and '/' not in key_id:
      return f'{catalog_parent}/locations/{location}/semanticTagKeys/{key_id}'
  if '/' not in key:
    return f'{catalog_parent}/locations/{location}/semanticTagKeys/{key}'
  raise calliope_exceptions.InvalidArgumentException(
      '--key',
      f'Invalid Semantic Tag Key [{key}]. Must be a key ID (for example,'
      ' `costcenter.allocation`) or a full resource name (`projects/'
      'gcp-semantic-tags-catalog/locations/{location}/semanticTagKeys/{key}`).',
  )


def ValidateValueId(value_id: str, arg_name: str = 'VALUE_ID') -> str:
  """Validates a short SemanticTagValue ID."""
  if not _VALUE_ID_PATTERN.match(value_id):
    raise calliope_exceptions.InvalidArgumentException(
        arg_name,
        f'Invalid Semantic Tag Value ID [{value_id}]. Must be 1-63 characters'
        ' consisting of letters, digits, hyphens, and underscores.',
    )
  return value_id


def ParseSemanticTagValueName(
    args,
    default_to_catalog: bool = False,
) -> tuple[str, str, str, str]:
  """Resolves a SemanticTagValue full resource name from VALUE_ID and flags.

  Args:
    args: Parsed command-line arguments containing `value_id`, `location`, and
      `parent`.
    default_to_catalog: Whether to default `--parent` to
      `projects/gcp-semantic-tags-catalog` when not specified.

  Returns:
    A 4-tuple of `(full_name, parent_location_container, location, value_id)`.
  """
  raw_value_id = args.value_id
  match = _VALUE_NAME_PATTERN.match(raw_value_id)
  if match:
    scope, scope_id, parsed_location, value_id = match.groups()
    parsed_parent = f'{scope}/{scope_id}'
    if (
        args.IsSpecified('parent')
        and ValidateParent(args.parent) != parsed_parent
    ):
      raise calliope_exceptions.InvalidArgumentException(
          '--parent',
          f'Parent [{args.parent}] conflicts with parent [{parsed_parent}] in'
          f' resource name [{raw_value_id}].',
      )
    if args.IsSpecified('location') and args.location != parsed_location:
      raise calliope_exceptions.InvalidArgumentException(
          '--location',
          f'Location [{args.location}] conflicts with location'
          f' [{parsed_location}] in resource name [{raw_value_id}].',
      )
    parent_location = f'{parsed_parent}/locations/{parsed_location}'
    return raw_value_id, parent_location, parsed_location, value_id

  if '/' in raw_value_id:
    raise calliope_exceptions.InvalidArgumentException(
        'VALUE_ID',
        f'Invalid Semantic Tag Value resource name [{raw_value_id}]. Must be a'
        ' short ID or in the format'
        ' {organizations|projects}/{id}/locations/{location}/'
        'semanticTagValues/{value_id}.',
    )

  ValidateValueId(raw_value_id)
  parent = GetParent(args, default_to_catalog=default_to_catalog)
  location = args.location or 'global'
  parent_location = f'{parent}/locations/{location}'
  full_name = f'{parent_location}/semanticTagValues/{raw_value_id}'
  return full_name, parent_location, location, raw_value_id


def ParseValueFile(
    file_path: str,
) -> tuple[str | None, dict[str, str] | None, str | None, str | None]:
  """Parses a YAML or JSON file for `semantic-tags values create --value-file`.

  Args:
    file_path: Path to the YAML or JSON file.

  Returns:
    A 4-tuple of `(string_value, composite_fields, display_name, description)`.
  """
  try:
    data = yaml.load_path(file_path)
  except yaml.Error as e:
    raise calliope_exceptions.InvalidArgumentException(
        '--value-file', f'Failed to parse value file [{file_path}]: {e}'
    )

  if not isinstance(data, dict) or not data:
    raise calliope_exceptions.InvalidArgumentException(
        '--value-file',
        f'Value file [{file_path}] must contain a non-empty YAML/JSON mapping.',
    )

  display_name = data.get('displayName') or data.get('display_name')
  description = data.get('description')

  if 'stringValue' in data or 'string_value' in data:
    raw_string = data.get('stringValue', data.get('string_value'))
    if raw_string is None or isinstance(raw_string, (dict, list)):
      raise calliope_exceptions.InvalidArgumentException(
          '--value-file',
          'Field `stringValue` in value file must be a scalar value.',
      )
    return str(raw_string), None, display_name, description

  composite_node = data.get('compositeValue') or data.get('composite_value')
  if isinstance(composite_node, dict) and 'fields' in composite_node:
    raw_fields = composite_node['fields']
  elif isinstance(composite_node, dict):
    raw_fields = composite_node
  elif 'fields' in data and isinstance(data['fields'], dict):
    raw_fields = data['fields']
  else:
    metadata_keys = {
        'displayName',
        'display_name',
        'description',
        'name',
        'semanticTagKey',
        'semantic_tag_key',
        'createTime',
        'create_time',
    }
    raw_fields = {k: v for k, v in data.items() if k not in metadata_keys}

  if not isinstance(raw_fields, dict) or not raw_fields:
    raise calliope_exceptions.InvalidArgumentException(
        '--value-file',
        f'Value file [{file_path}] must specify `compositeValue.fields` or'
        ' `stringValue`.',
    )

  composite_fields: dict[str, str] = {}
  for field_name, field_val in raw_fields.items():
    if isinstance(field_val, dict):
      if 'stringValue' in field_val:
        scalar_val = field_val['stringValue']
      elif 'string_value' in field_val:
        scalar_val = field_val['string_value']
      else:
        raise calliope_exceptions.InvalidArgumentException(
            '--value-file',
            f'Composite field [{field_name}] in [{file_path}] must contain'
            ' `stringValue`.',
        )
    elif isinstance(field_val, list) or field_val is None:
      raise calliope_exceptions.InvalidArgumentException(
          '--value-file',
          f'Composite field [{field_name}] in [{file_path}] must map to a'
          ' string value.',
      )
    else:
      scalar_val = field_val
    composite_fields[str(field_name)] = str(scalar_val)

  return None, composite_fields, display_name, description


def FormatSemanticValue(resource) -> str:
  """Formats SemanticTagValue oneof value (stringValue or compositeValue)."""
  if not isinstance(resource, dict):
    return ''
  if resource.get('stringValue'):
    return str(resource['stringValue'])
  fields = (resource.get('compositeValue') or {}).get('fields') or {}
  if isinstance(fields, dict):
    if 'additionalProperties' in fields and isinstance(
        fields['additionalProperties'], list
    ):
      pairs = {
          prop.get('key', ''): (prop.get('value') or {}).get('stringValue', '')
          for prop in fields['additionalProperties']
          if isinstance(prop, dict) and prop.get('key')
      }
    else:
      pairs = {
          k: v.get('stringValue', '') if isinstance(v, dict) else str(v)
          for k, v in fields.items()
      }
    if pairs:
      return ', '.join(f'{k}={v}' for k, v in sorted(pairs.items()))
  return ''


class SemanticTagValuesFilterRewriter(resource_expr_rewrite.Backend):
  """Filter expression rewriter for ListSemanticTagValues."""

  def __init__(self, location: str = 'global', **kwargs):
    super().__init__(**kwargs)
    self._location = location

  def RewriteTerm(self, key: str, op: str, operand, key_type):
    """Rewrites semanticTagKey filter terms into server-side AIP-160 syntax."""
    del key_type  # Unused.
    if key.lower() not in ('semantictagkey', 'semantic_tag_key'):
      return None
    if op != '=':
      return None
    if isinstance(operand, list):
      return None
    normalized_key = NormalizeSemanticTagKey(str(operand), self._location)
    return f'semantic_tag_key = "{normalized_key}"'


def NormalizeSemanticTagValue(
    value: str,
    parent: str | None = None,
    location: str = 'global',
) -> str:
  """Normalizes a SemanticTagValue reference into a full resource name."""
  if _VALUE_NAME_PATTERN.match(value):
    return value
  effective_parent = parent or GetCatalogParent()
  if value.startswith('locations/'):
    return f'{effective_parent}/{value}'
  if value.startswith('semanticTagValues/'):
    val_id = value.removeprefix('semanticTagValues/')
    return f'{effective_parent}/locations/{location}/semanticTagValues/{val_id}'
  if value and '/' not in value:
    return f'{effective_parent}/locations/{location}/semanticTagValues/{value}'
  return value


def ParseSemanticTagBindingName(args) -> tuple[str, str, str, str]:
  """Resolves a SemanticTagBinding full resource name from BINDING_NAME."""
  raw_name = args.binding_name
  match = _BINDING_NAME_PATTERN.match(raw_name)
  if match:
    scope, scope_id, parsed_location, binding_id = match.groups()
    parsed_parent = f'{scope}/{scope_id}'
    if (
        args.IsSpecified('parent')
        and ValidateParent(args.parent) != parsed_parent
    ):
      raise calliope_exceptions.InvalidArgumentException(
          '--parent',
          f'Parent [{args.parent}] conflicts with parent [{parsed_parent}] in'
          f' resource name [{raw_name}].',
      )
    if args.IsSpecified('location') and args.location != parsed_location:
      raise calliope_exceptions.InvalidArgumentException(
          '--location',
          f'Location [{args.location}] conflicts with location'
          f' [{parsed_location}] in resource name [{raw_name}].',
      )
    parent_location = f'{parsed_parent}/locations/{parsed_location}'
    return raw_name, parent_location, parsed_location, binding_id
  parent = GetParent(args, default_to_catalog=False)
  location = args.location or 'global'
  parent_location = f'{parent}/locations/{location}'
  if raw_name and '/' not in raw_name:
    full_name = f'{parent_location}/semanticTagBindings/{raw_name}'
  else:
    full_name = raw_name
  return full_name, parent_location, location, raw_name
