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
"""Resource arguments for Resource Manager Boundaries commands."""

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.resource_manager.boundaries import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs

API_VERSION = 'v3'


def OrgAttributeConfig():
  """Returns the resource parameter attribute config for organization."""
  return concepts.ResourceParameterAttributeConfig(
      name='organization',
      help_text='Organization ID or full resource name of the {resource}.',
      value_type=flags.ValidateOrganizationId,
  )


def FolderAttributeConfig():
  """Returns the resource parameter attribute config for folder."""
  return concepts.ResourceParameterAttributeConfig(
      name='folder',
      help_text='Folder ID or full resource name of the {resource}.',
      value_type=flags.ValidateFolderId,
  )


def BoundaryAttributeConfig():
  """Returns the resource parameter attribute config for boundary."""
  return concepts.ResourceParameterAttributeConfig(
      name='boundary',
      help_text='The boundary ID for the {resource}.',
  )


def GetOrgBoundaryResourceSpec():
  """Returns the ResourceSpec for an Organization Boundary."""
  return concepts.ResourceSpec(
      'cloudresourcemanager.organizations.boundaries',
      resource_name='boundary',
      organizationsId=OrgAttributeConfig(),
      boundariesId=BoundaryAttributeConfig(),
      api_version=API_VERSION,
  )


def GetFolderBoundaryResourceSpec():
  """Returns the ResourceSpec for a Folder Boundary."""
  return concepts.ResourceSpec(
      'cloudresourcemanager.folders.boundaries',
      resource_name='boundary',
      foldersId=FolderAttributeConfig(),
      boundariesId=BoundaryAttributeConfig(),
      api_version=API_VERSION,
  )


def GetBoundaryResourceSpec():
  """Returns the MultitypeResourceSpec for a Boundary."""
  return multitype.MultitypeResourceSpec(
      'boundary',
      GetOrgBoundaryResourceSpec(),
      GetFolderBoundaryResourceSpec(),
      allow_inactive=True,
  )


def AddBoundaryResourceArgToParser(parser, verb):
  """Adds a multitype resource argument for Boundary.

  Args:
    parser: The argparse parser.
    verb: str, the action being performed (e.g. 'to create').
  """
  concept_parsers.ConceptParser([
      presentation_specs.MultitypeResourcePresentationSpec(
          'boundary',
          GetBoundaryResourceSpec(),
          f'The boundary {verb}.',
          required=True,
      )
  ]).AddToParser(parser)


def ParseBoundary(args):
  """Parses and returns the Boundary Resource reference from args.

  Args:
    args: The parsed command line arguments.

  Returns:
    The Boundary Resource reference.
  """
  if '/' in (args.boundary or '') and (args.organization or args.folder):
    raise calliope_exceptions.InvalidArgumentException(
        'BOUNDARY',
        'Cannot specify --organization or --folder when a full boundary'
        ' resource name is provided.',
    )
  return args.CONCEPTS.boundary.Parse().result
