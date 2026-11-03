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
"""Cancel folder rollout command."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.PREVIEW)
@base.UniverseCompatible
class Cancel(base.Command):
  """Cancel Google Compute Engine folder rollouts."""

  detailed_help = {
      'brief': 'Cancel a folder rollout.',
      'DESCRIPTION': 'Cancel a folder rollout.',
      'EXAMPLES': (
          r"""
    To cancel a folder rollout named 'my-folder-rollout' in folder '123456789', run:

      $ {command} my-folder-rollout --folder=123456789
    """
      ),
  }

  @staticmethod
  def Args(parser):
    folder_rollout_resource_spec = concepts.ResourceSpec(
        'compute.folderRollouts',
        api_version='preview',
        resource_name='folder rollout',
        folder=concepts.ResourceParameterAttributeConfig(
            name='folder', help_text='The Google Cloud folder ID.'
        ),
        rollout=concepts.ResourceParameterAttributeConfig(
            name='name', help_text='Name of the folder rollout to cancel.'
        ),
    )
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        'name',
        folder_rollout_resource_spec,
        'Name of the folder rollout to cancel.',
        required=True,
    )
    concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)
    parser.add_argument(
        '--rollback',
        action='store_true',
        default=False,
        help="""
        If true, then the ongoing folder rollout must be rolled back. Else, just cancel
        the folder rollout without taking any further actions.
        """,
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(base.ReleaseTrack.PREVIEW)
    client = holder.client
    service = client.apitools_client.folderRollouts
    messages = holder.client.messages
    folder_rollout_ref = args.CONCEPTS.name.Parse()

    request = messages.ComputeFolderRolloutsCancelRequest(
        folder='folders/' + folder_rollout_ref.folder,
        rollout=folder_rollout_ref.Name(),
        rollback=args.rollback,
    )

    return service.Cancel(request)
