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
"""Create rollout plan command."""

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
  """Create a Google Compute Engine rollout plan."""

  detailed_help = {
      'brief': 'Create a Google Compute Engine rollout plan.',
      'DESCRIPTION': 'Create a Google Compute Engine rollout plan.',
      'EXAMPLES': (
          """\
        To create a rollout plan named `my-rollout-plan` from a wave definition
        file named `waves.json`, run:

          $ {command} my-rollout-plan --description="rollout plan description" --location-scope=ZONAL --waves-from-file=waves.json
        """
      ),
  }

  @staticmethod
  def Args(parser):
    rollout_plan_resource_spec = concepts.ResourceSpec(
        'compute.rolloutPlans',
        resource_name='rollout plan',
        rolloutPlan=concepts.ResourceParameterAttributeConfig(
            name='name', help_text='Name of rollout plan to create.'
        ),
        project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        api_version='beta',
    )
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        'name',
        rollout_plan_resource_spec,
        'Name of the rollout plan to create.',
        required=True,
    )
    concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)
    parser.add_argument(
        '--description', help='An optional description of this rollout plan.'
    )
    parser.add_argument(
        '--location-scope',
        choices=['ZONAL', 'REGIONAL'],
        default='ZONAL',
        help='The location scope of the rollout plan.',
    )
    parser.add_argument(
        '--waves-from-file',
        required=True,
        help=(
            'Path to a YAML or JSON file containing the wave definitions for'
            ' the rollout plan.'
        ),
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    rollout_plan_ref = args.CONCEPTS.name.Parse()

    waves = rollout_plans_util.LoadWavesFromFileAndAddToRequest(
        args.waves_from_file, messages
    )

    rollout_plan = messages.RolloutPlan(
        name=rollout_plan_ref.Name(),
        description=args.description,
        locationScope=messages.RolloutPlan.LocationScopeValueValuesEnum(
            args.location_scope
        ),
        waves=waves,
    )

    request = messages.ComputeRolloutPlansInsertRequest(
        project=rollout_plan_ref.project, rolloutPlan=rollout_plan
    )

    service = client.apitools_client.rolloutPlans
    operation = service.Insert(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.globalOperations'
    )

    log.CreatedResource(
        operation_ref,
        kind='rolloutPlan',
        is_async=True,
        details='Operation to create [{0}] in progress.'.format(
            rollout_plan_ref.Name()
        ),
    )
    return operation
