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
"""Command to list agent runtimes in Vertex AI."""

from googlecloudsdk.api_lib.ai.agent_runtimes import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai.agent_runtimes import agent_runtimes_util
from googlecloudsdk.core import resources


_DEFAULT_FORMAT = """
        table(
            name.basename():label=AGENT_RUNTIME_ID,
            displayName,
            createTime
        )
    """


def _GetUri(agent_runtime):
  ref = resources.REGISTRY.ParseRelativeName(
      agent_runtime.name,
      constants.AGENT_RUNTIMES_COLLECTION,
      api_version=constants.AI_PLATFORM_API_VERSION[constants.BETA_VERSION],
  )
  return ref.SelfLink()


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class List(base.ListCommand):
  """List the agent runtimes of a project and region.

  ## EXAMPLES

  To list the agent runtimes of project ``example'' in region ``us-central1'',
  run:

    $ {command} --project=example --region=us-central1
  """

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(_DEFAULT_FORMAT)
    parser.display_info.AddUriFunc(_GetUri)
    flags.AddRegionResourceArg(
        parser,
        'to list agent runtimes',
        prompt_func=region_util.GetPromptForRegionFunc(
            constants.SUPPORTED_AP_REGIONS
        ),
    )

  def Run(self, args):
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    agent_runtimes_util.ValidateRegion(region)

    with endpoint_util.AiplatformEndpointOverrides(
        constants.BETA_VERSION, region=region
    ):
      runtimes_client = client.AgentRuntimesClient(
          version=constants.BETA_VERSION
      )
      return agent_runtimes_util.WrapHttpErrors(
          runtimes_client.List(region=region_ref.RelativeName()),
          cmd_args=args,
      )
