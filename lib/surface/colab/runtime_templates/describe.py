# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Describe command for Colab Enterprise Runtime Templates."""

from googlecloudsdk.api_lib.colab_enterprise import runtime_templates as runtime_templates_util
from googlecloudsdk.api_lib.colab_enterprise import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.colab_enterprise import flags


_DETAILED_HELP = {
    'DESCRIPTION': """
        Describe a Colab Enterprise notebook runtime template.
    """,
    'EXAMPLES': """
        To describe a runtime template with id 'my-runtime-template' in region 'us-central1', run:

        $ {command} my-runtime-template --region=us-central1
    """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a runtime template."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddDescribeRuntimeTemplateFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    release_track = self.ReleaseTrack()
    messages = util.GetMessages(self.ReleaseTrack())
    runtime_template_ref = args.CONCEPTS.runtime_template.Parse()
    region = runtime_template_ref.AsDict()['locationsId']
    # Override to regionalize domain as used by the AIPlatform API.
    with endpoint_util.AiplatformEndpointOverrides(
        version='BETA', region=region
    ):
      api_client = util.GetClient(release_track)
      runtime_templates_service = (
          api_client.projects_locations_notebookRuntimeTemplates
      )
      return runtime_templates_service.Get(
          runtime_templates_util.CreateRuntimeTemplateGetRequest(
              args, messages
          )
      )


Describe.detailed_help = _DETAILED_HELP
