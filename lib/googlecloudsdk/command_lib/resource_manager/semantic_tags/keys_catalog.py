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
"""SemanticTagKey name helpers for Resource Manager Semantic Tags commands."""

import re
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import properties

# TODO: b/561830899 - Consolidate CATALOG_PARENT_PREFIX, _FULL_KEY_NAME_PATTERN,
# GetCatalogParent(), AddLocationArgToParser(), and NormalizeSemanticTagKey()
# with flags.py and utils.py once both the keys and values CLs land.
CATALOG_PARENT_PREFIX = 'projects/gcp-semantic-tags-catalog'
_FULL_KEY_NAME_PATTERN = re.compile(
    r'^(organizations/\d+|projects/[^/]+)/locations/([^/]+)/semanticTagKeys/([^/]+)$'
)
_KEY_RESOURCE_NAME_PATTERN = re.compile(
    r'^(?:(organizations/\d+|projects/[^/]+)/)?locations/([^/]+)/semanticTagKeys/([^/]+)$'
)


def GetCatalogParent() -> str:
  """Returns the GCP catalog parent resource name for the active CRM env."""
  endpoint = (
      properties.VALUES.api_endpoint_overrides.cloudresourcemanager.Get() or ''
  ).lower()
  if 'stagqual-' in endpoint or 'staging-' in endpoint:
    return f'{CATALOG_PARENT_PREFIX}-qual'
  if any(s in endpoint for s in ('autopush-', 'test-', '.sandbox.')):
    return f'{CATALOG_PARENT_PREFIX}-test'
  return CATALOG_PARENT_PREFIX


def AddLocationArgToParser(
    parser,
    required: bool = False,
    default: str | None = 'global',
    help_text: str = '',
):
  """Adds --location argument to the parser."""
  default_help = (
      'Location of the Semantic Tag resource (for example, `global` or'
      ' `us-central1`).'
  )
  kwargs = {
      'metavar': 'LOCATION',
      'required': required,
      'help': help_text or default_help,
  }
  if not required and default is not None:
    kwargs['default'] = default
  parser.add_argument('--location', **kwargs)


def NormalizeSemanticTagKey(
    key: str,
    location: str = 'global',
    arg_name: str = '--key',
) -> str:
  """Normalizes a SemanticTagKey reference into a full resource name."""
  if not key:
    raise calliope_exceptions.InvalidArgumentException(
        arg_name, 'Key cannot be empty.'
    )
  if _FULL_KEY_NAME_PATTERN.match(key):
    return key
  catalog = GetCatalogParent()
  if key.startswith('locations/'):
    full_key = f'{catalog}/{key}'
    if _FULL_KEY_NAME_PATTERN.match(full_key):
      return full_key
  if key.startswith('semanticTagKeys/'):
    key_id = key.removeprefix('semanticTagKeys/')
    if key_id and '/' not in key_id:
      return f'{catalog}/locations/{location}/semanticTagKeys/{key_id}'
  if '/' not in key:
    return f'{catalog}/locations/{location}/semanticTagKeys/{key}'
  raise calliope_exceptions.InvalidArgumentException(
      arg_name,
      f'Invalid Semantic Tag Key [{key}]. Must be a key ID (for example,'
      f' `placement.latency-optimized`) or a full resource name (`{catalog}/'
      'locations/{location}/semanticTagKeys/{key}`).',
  )


def ParseSemanticTagKeyName(args) -> tuple[str, str, str]:
  """Resolves a SemanticTagKey full resource name from KEY and --location."""
  raw_key = args.key
  match = _KEY_RESOURCE_NAME_PATTERN.match(raw_key)
  if match:
    _, parsed_location, _ = match.groups()
    if args.IsSpecified('location') and args.location != parsed_location:
      raise calliope_exceptions.InvalidArgumentException(
          '--location',
          f'Location [{args.location}] conflicts with location'
          f' [{parsed_location}] in resource name [{raw_key}].',
      )
    loc = parsed_location
  else:
    loc = args.location or 'global'
  full_name = NormalizeSemanticTagKey(raw_key, loc, arg_name='KEY')
  key_id = full_name.rsplit('/', 1)[-1]
  return full_name, loc, key_id
