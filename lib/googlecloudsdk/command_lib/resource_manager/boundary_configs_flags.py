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
"""Flags and helpers for CRM boundary-configs commands."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.resource_manager import completers


def AddParentFlagsToParser(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds parent resource argument (--organization or --folder) to parser."""
  parent_group = parser.add_mutually_exclusive_group(required=True)
  parent_group.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      completer=completers.OrganizationCompleter,
      help='Organization ID.',
  )
  parent_group.add_argument(
      '--folder',
      metavar='FOLDER_ID',
      help='Folder ID.',
  )


def AddTagKeyFlagsToParser(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds --tag-key and --clear-tag-key arguments to parser."""
  tag_key_group = parser.add_mutually_exclusive_group(required=True)
  tag_key_group.add_argument(
      '--tag-key',
      help='The namespaced name of the tag key (e.g. 123456789012/env).',
  )
  tag_key_group.add_argument(
      '--clear-tag-key',
      action='store_true',
      default=False,
      help='Clear the tag key from the boundary config.',
  )


def AddEtagArgToParser(parser: parser_arguments.ArgumentInterceptor) -> None:
  """Adds argument for the etag to the parser."""
  parser.add_argument(
      '--etag',
      help='The etag of the boundary config.',
  )


def AddAsyncFlagToParser(parser: parser_arguments.ArgumentInterceptor) -> None:
  """Adds --async flag to the parser."""
  base.ASYNC_FLAG.AddToParser(parser)


def GetParentFromFlags(args: parser_extensions.Namespace) -> str:
  """Gets the parent resource string from --organization or --folder flags."""
  if args.folder:
    folder_id = args.folder.removeprefix('folders/')
    if not folder_id.isdigit():
      raise calliope_exceptions.InvalidArgumentException(
          '--folder',
          f'Invalid folder ID [{args.folder}]. Must be a numeric ID or in the'
          ' format folders/{folder_id}.',
      )
    return f'folders/{folder_id}'

  org_id = args.organization.removeprefix('organizations/')
  if not org_id.isdigit():
    raise calliope_exceptions.InvalidArgumentException(
        '--organization',
        f'Invalid organization ID [{args.organization}]. Must be a numeric ID'
        ' or in the format organizations/{organization_id}.',
    )
  return f'organizations/{org_id}'


def GetBoundaryConfigResourceName(args: parser_extensions.Namespace) -> str:
  """Constructs the fully qualified boundaryConfig resource name."""
  return f'{GetParentFromFlags(args)}/boundaryConfig'
