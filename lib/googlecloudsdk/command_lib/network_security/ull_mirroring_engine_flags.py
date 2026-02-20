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
"""Flags for Ull Mirroring Engine commands."""

from googlecloudsdk.api_lib.network_security.ull_mirroring_engines import api
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs

ULL_MIRRORING_ENGINE_RESOURCE_NAME = 'ULL_MIRRORING_ENGINE'


def _UllMirroringEngineAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='ull_mirroring_engine',
      help_text='ID of the UllMirroringEngine for {resource}.',
  )


def _LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='The Cloud zone for the {resource}.',
  )


def AddUllMirroringEngineResource(parser, release_track):
  """Adds Ull Mirroring Engine resource to the parser."""
  resource_spec = concepts.ResourceSpec(
      'networksecurity.projects.locations.ullMirroringEngines',
      resource_name='ull_mirroring_engine',
      ullMirroringEnginesId=_UllMirroringEngineAttributeConfig(),
      locationsId=_LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
      api_version=api.GetApiVersion(release_track)

  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=ULL_MIRRORING_ENGINE_RESOURCE_NAME,
      concept_spec=resource_spec,
      required=True,
      group_help='The ULL Mirroring Engine.',
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)
