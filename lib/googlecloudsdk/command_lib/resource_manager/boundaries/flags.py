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
"""Flags and helpers for CRM boundaries commands."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.resource_manager import completers


def ValidateOrganizationId(value):
  """Validates and extracts the numeric organization ID."""
  org_id = value.removeprefix('organizations/')
  if not org_id.isdigit():
    raise calliope_exceptions.InvalidArgumentException(
        '--organization',
        f'Invalid organization ID [{value}]. Must be a numeric ID or in the'
        ' format organizations/{organization_id}.',
    )
  return org_id


def ValidateFolderId(value):
  """Validates and extracts the numeric folder ID."""
  folder_id = value.removeprefix('folders/')
  if not folder_id.isdigit():
    raise calliope_exceptions.InvalidArgumentException(
        '--folder',
        f'Invalid folder ID [{value}]. Must be a numeric ID or in the format'
        ' folders/{folder_id}.',
    )
  return folder_id


def AddParentFlagsToParser(parser):
  """Adds mutually exclusive --organization and --folder parent flags.

  Args:
    parser: The argparse parser.
  """
  mutex_group = parser.add_mutually_exclusive_group(
      required=True,
      help='Parent resource of the boundary.',
  )
  mutex_group.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      type=ValidateOrganizationId,
      completer=completers.OrganizationCompleter,
      help='Organization ID.',
  )
  mutex_group.add_argument(
      '--folder',
      metavar='FOLDER_ID',
      type=ValidateFolderId,
      help='Folder ID.',
  )


def AddDisplayNameArgToParser(parser, required=False):
  """Adds argument for the display name to the parser.

  Args:
    parser: The argparse parser.
    required: bool, whether the argument is required.
  """
  parser.add_argument(
      '--display-name',
      required=required,
      help='Friendly display name to use for the boundary.',
  )


def AddTagKeyArgToParser(parser, required=False):
  """Adds argument for the tag key to the parser.

  Args:
    parser: The argparse parser.
    required: bool, whether the argument is required.
  """
  parser.add_argument(
      '--tag-key',
      required=required,
      help='The namespaced name of the tag key (e.g. 123456789012/env).',
  )


def AddTagValueArgToParser(parser, required=False):
  """Adds argument for the tag value to the parser.

  Args:
    parser: The argparse parser.
    required: bool, whether the argument is required.
  """
  parser.add_argument(
      '--tag-value',
      required=required,
      help='The short name of the tag value (e.g. production).',
  )


def AddEtagArgToParser(parser):
  """Adds argument for the etag to the parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--etag',
      help='The etag of the boundary.',
  )


def AddAsyncFlagToParser(parser):
  """Adds --async flag to the parser.

  Args:
    parser: The argparse parser.
  """
  base.ASYNC_FLAG.AddToParser(parser)


def GetParentFromFlags(args):
  """Gets the parent resource string from --organization or --folder flags.

  Args:
    args: The parsed command line arguments.

  Returns:
    The parent resource string (e.g. 'organizations/123' or 'folders/456').
  """
  if args.folder:
    return f'folders/{args.folder}'
  return f'organizations/{args.organization}'
