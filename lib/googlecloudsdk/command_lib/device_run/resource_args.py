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
"""Shared resource arguments for Device Run commands."""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Cloud location for the {resource}.',
  )


def SessionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='session',
      help_text='The automation session ID.',
  )


def OperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='operation',
      help_text='The long-running operation ID.',
  )


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'devicerun.projects.locations',
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
  )


def GetSessionResourceSpec():
  return concepts.ResourceSpec(
      'devicerun.projects.locations.sessions',
      resource_name='session',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      sessionsId=SessionAttributeConfig(),
  )


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      'devicerun.projects.locations.operations',
      resource_name='operation',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      operationsId=OperationAttributeConfig(),
  )


def AddLocationResourceArg(parser, verb):
  concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      'Location to {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddSessionResourceArg(parser, verb, positional=True):
  concept_parsers.ConceptParser.ForResource(
      'session' if positional else '--session',
      GetSessionResourceSpec(),
      'Session to {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddOperationResourceArg(parser, verb, positional=True):
  concept_parsers.ConceptParser.ForResource(
      'operation' if positional else '--operation',
      GetOperationResourceSpec(),
      'Operation to {}.'.format(verb),
      required=True,
  ).AddToParser(parser)
