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
"""Flags for Resource Manager Semantic Tags commands."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


def AddValueIdArgToParser(parser, help_text: str):
  """Adds positional VALUE_ID argument to the parser."""
  parser.add_argument(
      'value_id',
      metavar='VALUE_ID',
      help=help_text,
  )


def AddKeyArgToParser(parser, required: bool = False, help_text: str = ''):
  """Adds --key argument to the parser."""
  default_help = (
      'Semantic Tag Key associated with the value. Accepts the full resource'
      ' name (`projects/gcp-semantic-tags-catalog/locations/{location}/'
      'semanticTagKeys/{key}`) or the key ID shorthand (for example,'
      ' `costcenter.allocation`).'
  )
  parser.add_argument(
      '--key',
      metavar='KEY',
      required=required,
      help=help_text or default_help,
  )


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


def AddParentArgToParser(parser, help_text: str = ''):
  """Adds --parent argument to the parser."""
  default_help = (
      'Parent container of the Semantic Tag Value in the form'
      ' `organizations/{organization_id}` or'
      ' `projects/{project_id_or_number}`. If not specified, defaults to the'
      ' active project (`projects/{core/project}`).'
  )
  parser.add_argument(
      '--parent',
      metavar='PARENT',
      help=help_text or default_help,
  )


def AddBindingParentArgToParser(parser, help_text: str = '') -> None:
  """Adds --parent argument for Semantic Tag Binding commands to the parser."""
  default_help = (
      'Parent container of the Semantic Tag Binding in the form'
      ' `organizations/{organization_id}` or'
      ' `projects/{project_id_or_number}`. For projects and project-scoped'
      ' subresources, bindings are stored under the project parent'
      ' (`projects/{project_id_or_number}`). For other Google Cloud resources'
      ' (such as organizations or folders), bindings are stored under the'
      ' organization parent (`organizations/{organization_id}`). If not'
      ' specified, defaults to the active project (`projects/{core/project}`).'
  )
  AddParentArgToParser(parser, help_text=help_text or default_help)


def AddBindingNameArgToParser(parser, help_text: str) -> None:
  """Adds positional BINDING_NAME argument to the parser."""
  parser.add_argument('binding_name', metavar='BINDING_NAME', help=help_text)


def AddTargetResourceArgToParser(
    parser, required: bool = True, help_text: str = ''
) -> None:
  """Adds --target-resource argument to the parser."""
  default_help = (
      'Full resource name of the target Google Cloud resource (for example,'
      # gcloud-disable-gdu-domain
      ' `//compute.googleapis.com/projects/my-proj/zones/us-central1-a/'
      'instances/vm-1` or `//cloudresourcemanager.googleapis.com/projects/'
      '123456`).'
  )
  parser.add_argument(
      '--target-resource',
      metavar='FULL_RESOURCE_URI',
      required=required,
      help=help_text or default_help,
  )


def AddSemanticTagValueArgToParser(
    parser, required: bool = True, help_text: str = ''
) -> None:
  """Adds --semantic-tag-value argument to the parser."""
  default_help = (
      'Resource name of the Semantic Tag Value being bound (for example,'
      ' `projects/my-proj/locations/global/semanticTagValues/val-1`,'
      ' `organizations/1001/locations/global/semanticTagValues/val-1`, or'
      ' `projects/gcp-semantic-tags-catalog/locations/global/'
      'semanticTagValues/prod`).'
  )
  parser.add_argument(
      '--semantic-tag-value',
      metavar='VALUE',
      required=required,
      help=help_text or default_help,
  )


def AddValueGroupToParser(parser):
  """Adds mutually exclusive value flags (--value, --value-field, --value-file)."""
  value_group = parser.add_mutually_exclusive_group(
      required=True,
      help='Value payload for the Semantic Tag Value.',
  )
  value_group.add_argument(
      '--value',
      metavar='STRING',
      help='Scalar string value for the Semantic Tag Value.',
  )
  value_group.add_argument(
      '--value-field',
      metavar='FIELD=VALUE',
      type=arg_parsers.ArgDict(key_type=str, value_type=str, min_length=1),
      action=arg_parsers.UpdateAction,
      help=(
          'Key-value pairs for a composite Semantic Tag Value (for example,'
          ' `--value-field=sre=40,infra=60` or'
          ' `--value-field=sre=40 --value-field=infra=60`).'
      ),
  )
  value_group.add_argument(
      '--value-file',
      metavar='FILE',
      help=(
          'Path to a YAML or JSON file defining a Semantic Tag Value payload'
          ' (containing `compositeValue`, and optionally `displayName` and'
          ' `description`).'
      ),
  )


def AddDisplayNameArgToParser(parser):
  """Adds --display-name argument to the parser."""
  parser.add_argument(
      '--display-name',
      metavar='DISPLAY_NAME',
      help='User-friendly display name for the Semantic Tag Value.',
  )


def AddDescriptionArgToParser(parser):
  """Adds --description argument to the parser."""
  parser.add_argument(
      '--description',
      metavar='DESCRIPTION',
      help='User-assigned description of the Semantic Tag Value.',
  )


def AddValidateOnlyArgToParser(parser, action_description: str = 'create'):
  """Adds --validate-only flag to the parser."""
  parser.add_argument(
      '--validate-only',
      action='store_true',
      default=False,
      help=(
          f'Validate the {action_description} request without actually'
          ' performing the operation.'
      ),
  )


def AddAsyncArgToParser(parser):
  """Adds --async flag to the parser."""
  base.ASYNC_FLAG.AddToParser(parser)
