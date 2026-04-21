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
"""Shared resource argument definitions for gcloud ai semantic-governance-policies."""

from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def semantic_governance_policy_attribute_config() -> (
    concepts.ResourceParameterAttributeConfig
):
  return concepts.ResourceParameterAttributeConfig(
      name='policy',
      help_text='ID of the semantic governance policy.',
  )


def get_semantic_governance_policy_resource_spec() -> concepts.ResourceSpec:
  """Returns a resource spec for a semantic governance policy."""
  return concepts.ResourceSpec(
      'aiplatform.projects.locations.semanticGovernancePolicies',
      resource_name='policy',
      semanticGovernancePoliciesId=semantic_governance_policy_attribute_config(),
      locationsId=flags.RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def add_semantic_governance_policy_resource_arg(
    parser: parser_extensions.ArgumentParser, verb: str
) -> None:
  """Adds a resource argument for a Vertex AI semantic governance policy.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: The verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'policy',
      get_semantic_governance_policy_resource_spec(),
      f'The semantic governance policy {verb}.',
      required=True,
  ).AddToParser(parser)
