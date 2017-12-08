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
"""'endpoints create' command."""

from googlecloudsdk.api_lib.service_registry import arg_support
from googlecloudsdk.api_lib.service_registry import constants
from googlecloudsdk.api_lib.service_registry import write_support
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Create(base.CreateCommand):
  """Create an endpoint entry in Service Registry."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To create an endpoint in Service Registry:

            $ {command} my_endpoint --target my_service.my_domain:8080 --networks NETWORK_URL

          For additional targets, just repeat the address flag, and to see
          more options use:

            $ {command} --help
          """,
  }

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
    """Runs 'endpoints create'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If --async=true, returns Operation to poll.
      Else, returns nothing.

    Raises:
      HttpException: An http error response was received while executing api
          request.
      ToolException: Endpoint creation encountered an error.
    """
    client = self.context[constants.CLIENT]
    messages = self.context[constants.MESSAGES]
    resources = self.context[constants.RESOURCES]
    project = properties.VALUES.core.project.Get(required=True)
    writer = write_support.ServiceRegistryClient(client, resources)

    request = messages.ServiceregistryEndpointsInsertRequest(
        project=project,
        endpoint=messages.Endpoint(
            name=args.endpoint_name,
            description=args.description,
            addresses=args.target,
            dnsIntegration=messages.EndpointDnsIntegration(
                networks=arg_support.ExpandNetworks(args.networks, project),
                enableExternal=args.enable_external,
            ),
        )
    )

    return writer.call_service_registry(
        client.endpoints.Insert, request, args.async, log.CreatedResource)
