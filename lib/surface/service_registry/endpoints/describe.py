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

"""'endpoints describe' command."""

from googlecloudsdk.api_lib.service_registry import arg_support
from googlecloudsdk.api_lib.service_registry import constants
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """Describe an endpoint entry in Service Registry."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To display information about an endpoint

            $ {command} ENDPOINT_NAME
          """,
  }

  @staticmethod
  def Args(parser):
    """Called by calliope to gather arguments for this command.

    Args:
      parser: argparse parser for specifying command line arguments
    """
    arg_support.AddEndpointNameArg(parser)

  def Run(self, args):
    """Runs 'endpoints describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The requested Endpoint.

    Raises:
      HttpException: An http error response was received while executing the api
          request.
      InvalidArgumentException: The requested endpoint could not be found.
    """
    client = self.context[constants.CLIENT]
    resources = self.context[constants.RESOURCES]
    endpoint_ref = resources.Parse(args.endpoint_name,
                                   collection=constants.ENDPOINTS_COLLECTION)

    request = client.MESSAGES_MODULE.ServiceregistryEndpointsGetRequest(
        project=endpoint_ref.project, endpoint=endpoint_ref.endpoint)
    return client.endpoints.Get(request)
