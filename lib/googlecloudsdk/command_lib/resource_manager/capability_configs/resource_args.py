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
"""Resource arguments for Resource Manager CapabilityConfigs commands."""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs

API_VERSION = 'v3'


def OrgAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='organization',
      help_text='Organization ID or full resource name of the {resource}.',
  )


def FolderAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='folder',
      help_text='Folder ID or full resource name of the {resource}.',
  )


def ProjectAttributeConfig():
  return concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG


def CapabilityConfigAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='capability_config',
      help_text='The CapabilityConfig ID for the {resource}.',
  )


def GetOrgCapabilityConfigResourceSpec():
  return concepts.ResourceSpec(
      'cloudresourcemanager.organizations.capabilityConfigs',
      resource_name='capability config',
      organizationsId=OrgAttributeConfig(),
      capabilityConfigsId=CapabilityConfigAttributeConfig(),
      api_version=API_VERSION,
  )


def GetFolderCapabilityConfigResourceSpec():
  return concepts.ResourceSpec(
      'cloudresourcemanager.folders.capabilityConfigs',
      resource_name='capability config',
      foldersId=FolderAttributeConfig(),
      capabilityConfigsId=CapabilityConfigAttributeConfig(),
      api_version=API_VERSION,
  )


def GetProjectCapabilityConfigResourceSpec():
  return concepts.ResourceSpec(
      'cloudresourcemanager.projects.capabilityConfigs',
      resource_name='capability config',
      projectsId=ProjectAttributeConfig(),
      capabilityConfigsId=CapabilityConfigAttributeConfig(),
      api_version=API_VERSION,
  )


def GetCapabilityConfigResourceSpec():
  return multitype.MultitypeResourceSpec(
      'capability_config',
      GetOrgCapabilityConfigResourceSpec(),
      GetFolderCapabilityConfigResourceSpec(),
      GetProjectCapabilityConfigResourceSpec(),
      allow_inactive=True,
  )


def AddCapabilityConfigResourceArgToParser(
    parser, verb, positional=True, required=True
):
  """Adds a multitype resource argument for CapabilityConfig."""
  name = 'capability_config' if positional else '--capability-config'
  spec = GetCapabilityConfigResourceSpec()
  concept_parsers.ConceptParser([
      presentation_specs.MultitypeResourcePresentationSpec(
          name,
          spec,
          'The CapabilityConfig {}.'.format(verb),
          required=required,
      )
  ]).AddToParser(parser)


def ParseCapabilityConfig(args):
  """Parses and returns the CapabilityConfig Resource reference from args."""
  concept_result = args.CONCEPTS.capability_config.Parse()
  return concept_result.result if concept_result else None
