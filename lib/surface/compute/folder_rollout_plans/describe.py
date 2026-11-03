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
"""Describe folder rollout plan command."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.PREVIEW)
@base.UniverseCompatible
class Describe(base.DescribeCommand):
  """Describe a folder rollout plan."""

  detailed_help = {
      'brief': 'Describe a folder rollout plan.',
      'DESCRIPTION': 'Describe a folder rollout plan.',
      'EXAMPLES': (
          r"""
    To describe a folder rollout plan named 'my-folder-rollout-plan' in folder '123456789', run:

      $ {command} my-folder-rollout-plan --folder=123456789
    """
      ),
  }

  @staticmethod
  def Args(parser):
    folder_rollout_plan_resource_spec = concepts.ResourceSpec(
        'compute.folderRolloutPlans',
        api_version='preview',
        resource_name='folder rollout plan',
        folder=concepts.ResourceParameterAttributeConfig(
            name='folder', help_text='The Google Cloud folder ID.'
        ),
        rolloutPlan=concepts.ResourceParameterAttributeConfig(
            name='name',
            help_text='Name of the folder rollout plan to describe.',
        ),
    )
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        'name',
        folder_rollout_plan_resource_spec,
        'Name of the folder rollout plan you want to inspect.',
        required=True,
    )
    concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(base.ReleaseTrack.PREVIEW)
    client = holder.client
    service = client.apitools_client.folderRolloutPlans
    messages = holder.client.messages
    folder_rollout_plan_ref = args.CONCEPTS.name.Parse()

    request = messages.ComputeFolderRolloutPlansGetRequest(
        folder='folders/' + folder_rollout_plan_ref.folder,
        rolloutPlan=folder_rollout_plan_ref.Name(),
    )

    return service.Get(request)
