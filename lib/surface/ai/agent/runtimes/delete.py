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

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.agent_runtimes import client
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io

_AGENT_RUNTIME_DELETE_DISPLAY_MESSAGE = """\
Request to delete the agent runtime [{name}] has been sent.

You may view the status of your agent runtime with the command

  $ {command_prefix} ai agent runtimes describe {name}
"""


def _ParseOperation(operation_name):
  """Parse operation resource name to the operation reference object."""
  if '/reasoningEngines/' in operation_name:
    try:
      return resources.REGISTRY.ParseRelativeName(
          operation_name,
          collection=(
              'aiplatform.projects.locations.reasoningEngines.operations'
          ),
      )
    except resources.WrongResourceCollectionException:
      pass
  return resources.REGISTRY.ParseRelativeName(
      operation_name, collection='aiplatform.projects.locations.operations'
  )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
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

  def _CommandPrefix(self):
    cmd_prefix = 'gcloud'
    if self.ReleaseTrack().prefix:
      cmd_prefix += ' ' + self.ReleaseTrack().prefix
    return cmd_prefix

  def Run(self, args):
    runtime_ref = args.CONCEPTS.runtime.Parse()
    region = runtime_ref.AsDict()['locationsId']
    if properties.IsDefaultUniverse():
      validation.ValidateRegion(
          region, available_regions=constants.SUPPORTED_AP_REGIONS
      )
    console_io.PromptContinue(
        'This will delete agent runtime [{}]...'.format(runtime_ref.Name()),
        cancel_on_no=True,
    )
    with endpoint_util.AiplatformEndpointOverrides(
        constants.BETA_VERSION, region=region
    ):
      resource_name = runtime_ref.RelativeName()
      try:
        operation = client.AgentRuntimesClient(
            version=constants.BETA_VERSION
        ).Delete(resource_name, force=args.force)
      except apitools_exceptions.HttpError as error:
        # Translates generic HTTP error into a user-friendly gcloud exception
        raise api_exceptions.HttpException(
            error,
            'ResponseError: code={status_code}, message={status_message}',
        )
      response = operations_util.WaitForOpMaybe(
          operations_client=operations.OperationsClient(),
          op=operation,
          op_ref=_ParseOperation(operation.name),
          asynchronous=args.async_,
      )
      if args.async_:
        log.status.Print(
            _AGENT_RUNTIME_DELETE_DISPLAY_MESSAGE.format(
                name=resource_name, command_prefix=self._CommandPrefix()
            )
        )
      else:
        log.DeletedResource(runtime_ref.Name(), kind='agent runtime')
      return response
