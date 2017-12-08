# Copyright 2016 Google Inc. All Rights Reserved.
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

"""endpoints update' command."""

from googlecloudsdk.api_lib.service_registry import arg_support
from googlecloudsdk.api_lib.service_registry import constants
from googlecloudsdk.api_lib.service_registry import write_support
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class Update(base.UpdateCommand):
  """Update an endpoint.

  This command updates the contents of an endpoint entry in Service Registry.

  ## EXAMPLES

  To update an endpoint in Service Registry:

    $ {command} ENDPOINT_NAME --target ADDRESS:PORT --networks NETWORK_URL

  For additional addresses, just repeat the --address flag, and to see
  more options be sure to use:

    $ {command} --help
  """

  @staticmethod
  def Args(parser):
    """Called by calliope to gather arguments for this command.

    Args:
      parser: argparse parser for specifying command line arguments
    """
    arg_support.AddEndpointNameArg(parser)
    arg_support.AddAsyncArg(parser)
    arg_support.AddTargetArg(parser)
    arg_support.AddNetworksArg(parser)
    arg_support.AddDescriptionArg(parser)
    arg_support.AddEnableExternalArg(parser)

  def Run(self, args):
    """Runs 'endpoints update'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If --async=true, returns Operation to poll.
      Else returns nothing.

    Raises:
      HttpException: An http error response was received while executing api
          request.
      ToolException: Endpoint update encountered an error.
    """
    client = self.context[constants.CLIENT]
    messages = self.context[constants.MESSAGES]
    resources = self.context[constants.RESOURCES]
    project = properties.VALUES.core.project.Get(required=True)
    writer = write_support.ServiceRegistryClient(client, resources)

    fingerprint = None
    endpoint = client.endpoints.Get(
        messages.ServiceregistryEndpointsGetRequest(
            project=project, endpoint=args.endpoint_name))
    fingerprint = endpoint.fingerprint

    message_str = 'Preparing to update [{0}].'.format(args.endpoint_name)
    if not console_io.PromptContinue(message=message_str):
      log.Print('Cancelling update operation.')
      return

    request = messages.ServiceregistryEndpointsUpdateRequest(
        project=project,
        endpoint=args.endpoint_name,
        endpointResource=messages.Endpoint(
            name=args.endpoint_name,
            description=args.description,
            addresses=args.target,
            dnsIntegration=messages.EndpointDnsIntegration(
                networks=arg_support.ExpandNetworks(args.networks, project),
                enableExternal=args.enable_external,
            ),
            fingerprint=fingerprint
        )
    )

    return writer.call_service_registry(
        client.endpoints.Update, request, args.async, log.UpdatedResource)
