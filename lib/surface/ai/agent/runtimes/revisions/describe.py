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
"""Command to describe an agent runtime revision."""

from googlecloudsdk.api_lib.ai.agent_runtimes import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai.agent_runtimes import agent_runtimes_util


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class Describe(base.DescribeCommand):
  """Get detailed information about an agent runtime revision with a given id.

  ## EXAMPLES

  To describe the revision with id ``123'' of agent runtime ``456'' under
  project ``example'' in region ``us-central1'', run:

    $ {command} 123 --runtime=456 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddAgentRuntimeRevisionResourceArg(parser, 'to describe')

  def Run(self, args):
    revision_ref = args.CONCEPTS.revision.Parse()
    region = revision_ref.AsDict()['locationsId']
    agent_runtimes_util.ValidateRegion(region)
    with endpoint_util.AiplatformEndpointOverrides(
        constants.BETA_VERSION, region=region
    ):
      runtimes_client = client.AgentRuntimesClient(
          version=constants.BETA_VERSION
      )
      return agent_runtimes_util.ExecuteApiCall(
          runtimes_client.GetRevision,
          revision_ref.RelativeName(),
          cmd_args=args,
      )
