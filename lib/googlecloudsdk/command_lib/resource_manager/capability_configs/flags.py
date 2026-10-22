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
"""Flags and arguments for Resource Manager CapabilityConfigs commands."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as calliope_exceptions


def ValidateOrganizationId(value: str) -> str:
  """Validates and extracts the numeric organization ID."""
  org_id = value.removeprefix('organizations/')
  if not org_id.isdigit():
    raise calliope_exceptions.InvalidArgumentException(
        '--organization',
        f'Invalid organization ID [{value}]. Must be a numeric ID or in the'
        ' format organizations/{organization_id}.',
    )
  return org_id


def ValidateFolderId(value: str) -> str:
  """Validates and extracts the numeric folder ID."""
  folder_id = value.removeprefix('folders/')
  if not folder_id.isdigit():
    raise calliope_exceptions.InvalidArgumentException(
        '--folder',
        f'Invalid folder ID [{value}]. Must be a numeric ID or in the format'
        ' folders/{folder_id}.',
    )
  return folder_id


def ValidateProject(value: str) -> str:
  """Validates and extracts the numeric project number."""
  project_number = value.removeprefix('projects/')
  if not project_number.isdigit():
    raise calliope_exceptions.InvalidArgumentException(
        '--project',
        f'Invalid project number [{value}]. Must be a project number or in the'
        ' format projects/{project_number}.',
    )
  return project_number


def AddParentFlagsToParser(parser, message):
  """Adds parent flags (--organization, --folder, --project) to the parser."""
  mutex_group = parser.add_group(
      mutex=True,
      required=True,
      help=f'Parent resource {message}.',
  )
  mutex_group.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      type=ValidateOrganizationId,
      help='Organization ID or full resource name.',
  )
  mutex_group.add_argument(
      '--folder',
      metavar='FOLDER_ID',
      type=ValidateFolderId,
      help='Folder ID or full resource name.',
  )
  mutex_group.add_argument(
      '--project',
      metavar='PROJECT_NUMBER',
      type=ValidateProject,
      help='Project number or full resource name.',
  )


def GetParentFromArgs(args):
  """Extracts parent relative name from args."""
  if getattr(args, 'organization', None):
    org = args.organization
    return org if org.startswith('organizations/') else f'organizations/{org}'
  if getattr(args, 'folder', None):
    folder = args.folder
    return folder if folder.startswith('folders/') else f'folders/{folder}'
  if getattr(args, 'project', None):
    project = args.project
    return project if project.startswith('projects/') else f'projects/{project}'

  raise calliope_exceptions.RequiredArgumentException(
      '--organization, --folder, or --project',
      'Please specify a parent resource.',
  )


def AddTypesArgToParser(parser, required=False):
  """Adds the --types argument to the parser."""
  parser.add_argument(
      '--types',
      type=arg_parsers.ArgList(
          choices=['app-management', 'agent-management'],
      ),
      metavar='TYPES',
      required=required,
      help=(
          'Comma-separated list of CapabilityConfig types (e.g. app-management,'
          ' agent-management).'
      ),
  )


def AddDisplayNameArgToParser(parser):
  """Adds the --display-name argument to the parser."""
  parser.add_argument(
      '--display-name',
      help=(
          'Human-readable display name of the CapabilityConfig (4 to 30'
          ' characters).'
      ),
  )


def AddManagementProjectArgToParser(parser):
  """Adds the --management-project argument to the parser."""
  parser.add_argument(
      '--management-project',
      help=(
          'Management Project associated with this CapabilityConfig (e.g.'
          ' projects/123456789012).'
      ),
  )


def AddBoundariesArgToParser(parser):
  """Adds the --boundaries argument to the parser."""
  parser.add_argument(
      '--boundaries',
      type=arg_parsers.ArgList(),
      metavar='BOUNDARIES',
      help='List of Boundaries associated with this CapabilityConfig.',
  )


def AddClearBoundariesArgToParser(parser):
  """Adds the --clear-boundaries argument to the parser."""
  parser.add_argument(
      '--clear-boundaries',
      action='store_true',
      default=False,
      help='Clear all Boundaries associated with this CapabilityConfig.',
  )


def AddEtagArgToParser(parser):
  """Adds the --etag argument to the parser."""
  parser.add_argument(
      '--etag',
      help='Etag string for optimistic concurrency control.',
  )
