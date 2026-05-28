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
"""Create organization rollout plan command."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.compute.rollout_plans import rollout_plans_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.UniverseCompatible
class Create(base.CreateCommand):
  """Create a Google Compute Engine organization rollout plan."""

  detailed_help = {
      'brief': 'Create an organization rollout plan.',
      'DESCRIPTION': (
          'Create a Google Compute Engine organization rollout plan.'
      ),
      'EXAMPLES': (
          """\
        To create an organization rollout plan named `my-org-rollout-plan` from a wave definition
        file named `waves.json` under organization `123456789`, run:

          $ {command} my-org-rollout-plan --organization=123456789 --waves-from-file=waves.json
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
            help_text='Name of the organization rollout plan to create.',
        ),
        api_version='beta',
    )
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        'name',
        org_rollout_plan_resource_spec,
        'Name of the organization rollout plan to create.',
        required=True,
    )
    concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)
    parser.add_argument(
        '--description',
        help='An optional description of this organization rollout plan.',
    )
    parser.add_argument(
        '--location-scope',
        choices=['ZONAL', 'REGIONAL'],
        default='ZONAL',
        help='The location scope of the organization rollout plan.',
    )
    parser.add_argument(
        '--waves-from-file',
        required=True,
        help=(
            'Path to a YAML or JSON file containing the wave definitions for'
            ' the organization rollout plan.'
        ),
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    org_rollout_plan_ref = args.CONCEPTS.name.Parse()

    waves = rollout_plans_util.LoadWavesFromFileAndAddToRequest(
        args.waves_from_file, messages
    )

    org_rollout_plan = messages.RolloutPlan(
        name=org_rollout_plan_ref.Name(),
        description=args.description,
        locationScope=messages.RolloutPlan.LocationScopeValueValuesEnum(
            args.location_scope
        ),
        waves=waves,
    )

    request = messages.ComputeOrganizationRolloutPlansInsertRequest(
        organization='organizations/' + org_rollout_plan_ref.organizationsId,
        rolloutPlan=org_rollout_plan,
    )

    service = client.apitools_client.organizationRolloutPlans
    operation = service.Insert(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.globalOrganizationOperations'
    )

    log.CreatedResource(
        operation_ref,
        kind='organizationRolloutPlan',
        is_async=True,
        details='Operation to create [{0}] in progress.'.format(
            org_rollout_plan_ref.Name()
        ),
    )
    return operation
