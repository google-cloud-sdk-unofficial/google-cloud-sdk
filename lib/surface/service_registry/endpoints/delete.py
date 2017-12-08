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

"""'endpoints delete' command."""

from googlecloudsdk.api_lib.service_registry import arg_support
from googlecloudsdk.api_lib.service_registry import constants
from googlecloudsdk.api_lib.service_registry import write_support
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class Delete(base.Command):
  """Delete an endpoint.

  This command deletes an endpoint entry in Service Registry.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To delete an endpoint in Service Registry

            $ {command} ENDPOINT_NAME

          And if you don't want to wait to see if the asynchronous delete was
          successful, you can use the --async flag to have an Operation
          returned immediately

            $ {command} ENDPOINT_NAME --async
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

  def Run(self, args):
    """Runs 'endpoints delete'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If --async=true, returns Operation to poll.
      Else, returns nothing.

    Raises:
      HttpException: An http error response was received while executing api
          request.
      ToolException: The endpoint deletion operation encountered an error.
    """
    client = self.context[constants.CLIENT]
    messages = self.context[constants.MESSAGES]
    resources = self.context[constants.RESOURCES]
    project = properties.VALUES.core.project.Get(required=True)
    writer = write_support.ServiceRegistryClient(client, resources)

    request = messages.ServiceregistryEndpointsDeleteRequest(
        project=project,
        endpoint=args.endpoint_name
    )

    return writer.call_service_registry(
        client.endpoints.Delete, request, args.async,
        'Deleted [{0}] successfully.'.format(args.endpoint_name))
