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
"""Advance organization rollout command."""

from typing import Any

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class Advance(base.Command):
  """Advance a Google Compute Engine organization rollout."""

  detailed_help = {
      'brief': 'Advance an organization rollout.',
      'DESCRIPTION': 'Advance an organization rollout.',
      'EXAMPLES': (
          r"""
    To advance an organization rollout named 'my-org-rollout' in organization '123456789' from wave 2 to the next wave, run:

      $ {command} my-org-rollout --organization=123456789 --current-wave-number=2
    """
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    org_rollout_resource_spec = concepts.ResourceSpec(
        'compute.organizationRollouts',
        api_version='alpha',
        resource_name='organization rollout',
        organizationsId=concepts.ResourceParameterAttributeConfig(
            name='organization', help_text='The Google Cloud organization ID.'
        ),
        rollout=concepts.ResourceParameterAttributeConfig(
            name='name',
            help_text='Name of the organization rollout to advance.',
        ),
    )
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        'name',
        org_rollout_resource_spec,
        'Name of the organization rollout to advance.',
        required=True,
    )
    concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)
    parser.add_argument(
        '--current-wave-number',
        type=int,
        required=True,
        help="""
        Wave number of the current wave to be used for advancing the rollout.
        """,
    )

  def Run(self, args: parser_extensions.Namespace) -> Any:
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    service = client.apitools_client.organizationRollouts
    messages = holder.client.messages
    org_rollout_ref = args.CONCEPTS.name.Parse()

    request = messages.ComputeOrganizationRolloutsAdvanceRequest(
        organization='organizations/' + org_rollout_ref.organizationsId,
        rollout=org_rollout_ref.Name(),
        currentWaveNumber=args.current_wave_number,
    )

    return service.Advance(request)
