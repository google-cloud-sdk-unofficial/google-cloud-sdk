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

"""Shared resource flags for BeyondCorp commands."""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def ProjectAttributeConfig():
  """Returns the project attribute config."""
  return concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG


def LocationAttributeConfig():
  """Returns the location attribute config."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='The location id. We support only global location.')


def SecurityGatewayAttributeConfig():
  """Returns the security gateway attribute config."""
  return concepts.ResourceParameterAttributeConfig(
      name='security-gateway',
      help_text='The security gateway ID.')


def ApplicationAttributeConfig():
  """Returns the application attribute config."""
  return concepts.ResourceParameterAttributeConfig(
      name='application',
      help_text='The application ID.')


def GetSecurityGatewayResourceSpec():
  """Returns the resource spec for a Security Gateway."""
  return concepts.ResourceSpec(
      'beyondcorp.projects.locations.securityGateways',
      resource_name='security_gateway',
      projectsId=ProjectAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      securityGatewaysId=SecurityGatewayAttributeConfig())


def GetApplicationResourceSpec():
  """Returns the resource spec for a Application."""
  return concepts.ResourceSpec(
      'beyondcorp.projects.locations.securityGateways.applications',
      resource_name='application',
      projectsId=ProjectAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      securityGatewaysId=SecurityGatewayAttributeConfig(),
      applicationsId=ApplicationAttributeConfig())


def AddSecurityGatewayResourceArg(parser, help_text):
  """Adds a resource argument for a Security Gateway."""
  concept_parsers.ConceptParser.ForResource(
      'security_gateway',
      GetSecurityGatewayResourceSpec(),
      help_text,
      required=True).AddToParser(parser)


def AddApplicationResourceArg(parser, help_text):
  """Adds a resource argument for a Application."""
  concept_parsers.ConceptParser.ForResource(
      'application',
      GetApplicationResourceSpec(),
      help_text,
      required=True).AddToParser(parser)
