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
"""Shared resource args for App Topology surface."""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def DefaultToGlobal():
  """Returns 'global' as fallthrough hook for location resolution."""
  return 'global'


def _DefaultToGlobalLocationAttributeConfig(help_text=None):
  """Creates location attribute config with automatic fallthrough to 'global'.

  Args:
    help_text: str or None, Custom help text for the location attribute.

  Returns:
    concepts.ResourceParameterAttributeConfig: Configured attribute config.
  """
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      fallthroughs=[
          deps.Fallthrough(
              function=DefaultToGlobal,
              hint='App Topology currently supports global location by default',
          )
      ],
      help_text=help_text
      or ('Location for the {resource}. Defaults to "global".'),
  )


def GetGlobalLocationResourceSpec():
  """Returns resource spec for location with global default."""
  return concepts.ResourceSpec(
      'apptopology.projects.locations',
      resource_name='location',
      locationsId=_DefaultToGlobalLocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def GetLocationResourceSpec():
  """Returns resource spec for an explicit location."""
  return concepts.ResourceSpec(
      'apptopology.projects.locations',
      resource_name='location',
      locationsId=concepts.ResourceParameterAttributeConfig(
          name='location',
          help_text='The Cloud location for the {resource}.',
      ),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def GetDomainResourceSpec():
  """Returns the resource specification for an App Topology domain."""
  return concepts.ResourceSpec(
      'apptopology.projects.locations.domains',
      resource_name='domain',
      domainsId=concepts.ResourceParameterAttributeConfig(
          name='domain',
          help_text='The App Topology domain name.',
      ),
      locationsId=_DefaultToGlobalLocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddLocationResourceArg(parser, verb='to operate on'):
  """Adds a resource argument for an App Topology location to the parser.

  Args:
    parser: googlecloudsdk.calliope.parser_arguments.ArgumentInterceptor, The
      argument parser.
    verb: str, The action verb to include in the help text (e.g. 'to list').
  """
  concept_parsers.ConceptParser.ForResource(
      '--location',
      GetGlobalLocationResourceSpec(),
      f'The location {verb}.',
      required=False,
  ).AddToParser(parser)


def AddDomainResourceArg(parser, verb='to operate on', positional=True):
  """Adds a resource argument for an App Topology domain to the parser.

  Args:
    parser: googlecloudsdk.calliope.parser_arguments.ArgumentInterceptor, The
      argument parser.
    verb: str, The action verb to include in the help text (e.g. 'to describe').
    positional: bool, Whether to add DOMAIN as a positional argument (True) or
      flag (False).
  """
  name = 'DOMAIN' if positional else '--domain'
  concept_parsers.ConceptParser.ForResource(
      name, GetDomainResourceSpec(), f'The domain {verb}.', required=True
  ).AddToParser(parser)
