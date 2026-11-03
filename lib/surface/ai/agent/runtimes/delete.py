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
"""Command to delete an agent runtime in Vertex AI."""

from googlecloudsdk.api_lib.ai.agent_runtimes import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai.agent_runtimes import agent_runtimes_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

_AGENT_RUNTIME_DELETE_DISPLAY_MESSAGE = """\
Request to delete the agent runtime [{name}] has been sent.
Operation: [{operation_name}]

You may view the status of your agent runtime with the command

  $ {command_prefix} ai agent runtimes describe {name}
"""


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class Delete(base.DeleteCommand):
  """Delete an existing agent runtime.

  ## EXAMPLES

  To delete an agent runtime ``123'' under project ``example'' in region
  ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddAgentRuntimeResourceArg(parser, 'to delete')
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        '--force',
        action='store_true',
        default=False,
        help=(
            'If set to true, child resources of this agent runtime will also be'
            ' deleted.'
        ),
    )

  def Run(self, args):
    runtime_ref = args.CONCEPTS.runtime.Parse()
    region = runtime_ref.AsDict()['locationsId']
    agent_runtimes_util.ValidateRegion(region)
    console_io.PromptContinue(
        'This will delete agent runtime [{}]...'.format(runtime_ref.Name()),
        cancel_on_no=True,
    )
    with endpoint_util.AiplatformEndpointOverrides(
        constants.BETA_VERSION, region=region
    ):
      resource_name = runtime_ref.RelativeName()
      runtimes_client = client.AgentRuntimesClient(
          version=constants.BETA_VERSION
      )
      operation = agent_runtimes_util.ExecuteApiCall(
          runtimes_client.Delete,
          resource_name,
          force=args.force,
          cmd_args=args,
      )
      response, _ = agent_runtimes_util.WaitForOperation(
          operation,
          asynchronous=args.async_,
          cmd_args=args,
      )
      if args.async_:
        log.status.Print(
            _AGENT_RUNTIME_DELETE_DISPLAY_MESSAGE.format(
                name=resource_name,
                operation_name=operation.name,
                command_prefix=agent_runtimes_util.CommandPrefix(
                    self.ReleaseTrack()
                ),
            )
        )
      else:
        log.DeletedResource(runtime_ref.Name(), kind='agent runtime')
      return response
