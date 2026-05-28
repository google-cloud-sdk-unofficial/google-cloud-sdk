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
"""Delete organization rollout plan command."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.UniverseCompatible
class Delete(base.DeleteCommand):
  """Delete Google Compute Engine organization rollout plans."""

  detailed_help = {
      'brief': 'Delete an organization rollout plan.',
      'DESCRIPTION': (
          'Delete a Google Compute Engine organization rollout plan.'
      ),
      'EXAMPLES': (
          r"""
    To delete an organization rollout plan named 'my-org-rollout-plan' in organization '123456789', run:

      $ {command} my-org-rollout-plan --organization=123456789
    """
      ),
  }

  @staticmethod
  def Args(parser):
    org_rollout_plan_resource_spec = concepts.ResourceSpec(
        'compute.organizationRolloutPlans',
        resource_name='organization rollout plan',
        organizationsId=concepts.ResourceParameterAttributeConfig(
            name='organization', help_text='The Google Cloud organization ID.'
        ),
        rolloutPlan=concepts.ResourceParameterAttributeConfig(
            name='name',
            help_text='Name of the organization rollout plan to delete.',
        ),
        api_version='beta',
    )
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        'name',
        org_rollout_plan_resource_spec,
        'Name of the organization rollout plan to delete.',
        required=True,
    )
    concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    service = client.apitools_client.organizationRolloutPlans
    messages = holder.client.messages
    org_rollout_plan_ref = args.CONCEPTS.name.Parse()

    request = messages.ComputeOrganizationRolloutPlansDeleteRequest(
        organization='organizations/' + org_rollout_plan_ref.organizationsId,
        rolloutPlan=org_rollout_plan_ref.Name(),
    )

    return service.Delete(request)
