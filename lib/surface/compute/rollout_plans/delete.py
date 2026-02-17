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
"""Delete rollout plan command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.UniverseCompatible
class Delete(base.DeleteCommand):
  """Delete Google Compute Engine rollout plans."""

  detailed_help = {
      'brief': 'Delete a Google Compute Engine rollout plan.',
      'DESCRIPTION': 'Delete a Google Compute Engine rollout plan.',
      'EXAMPLES': (
          r"""
    To delete a rollout plan named 'my-rollout-plan', run:

      $ {command} my-rollout-plan
    """
      ),
  }

  @staticmethod
  def Args(parser):
    rollout_plan_resource_spec = concepts.ResourceSpec(
        'compute.rolloutPlans',
        resource_name='rollout plan',
        rolloutPlan=concepts.ResourceParameterAttributeConfig(
            name='name', help_text='Name of rollout plan to delete.'
        ),
        project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        api_version='beta',
    )
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        'name',
        rollout_plan_resource_spec,
        'Name of the rollout plan to delete.',
        required=True,
    )
    concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    service = client.apitools_client.rolloutPlans
    messages = holder.client.messages
    rollout_plan_ref = args.CONCEPTS.name.Parse()

    request = messages.ComputeRolloutPlansDeleteRequest(
        project=rollout_plan_ref.project, rolloutPlan=rollout_plan_ref.Name()
    )

    return service.Delete(request)
