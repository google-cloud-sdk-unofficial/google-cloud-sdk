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
"""Shared resource argument utilities for Firestore commands."""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def DatabaseAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='database',
      fallthroughs=[
          deps.ArgFallthrough('--database'),
          deps.Fallthrough(
              lambda: '(default)',
              hint='the default value of argument [--database] is `(default)`',
          ),
      ],
      help_text='Database of the {resource}.',
  )


def CollectionGroupAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='collection-group',
      help_text='Collection group of the {resource}.',
  )


def GetCollectionGroupResourceSpec():
  return concepts.ResourceSpec(
      'firestore.projects.databases.collectionGroups',
      resource_name='collection group',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      databasesId=DatabaseAttributeConfig(),
      collectionGroupsId=CollectionGroupAttributeConfig(),
  )


def AddCollectionGroupResourceArg(parser):
  concept_parsers.ConceptParser.ForResource(
      '--collection-group',
      GetCollectionGroupResourceSpec(),
      'Collection group of the index.',
      required=True,
  ).AddToParser(parser)
