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

"""'operations describe' command."""

from googlecloudsdk.api_lib.service_registry import constants
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """Describe an operation.

  This command describes an operation in Service Registry.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To display information about an operation, run:

            $ {command} OPERATION_NAME
          """,
  }

  @staticmethod
  def Args(parser):
    """Called by calliope to gather arguments for this command.

    Args:
      parser: argparse parser for specifying command line arguments
    """
    parser.add_argument('operation', help='Operation name.')

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Runs 'operations desrcribe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The requested Operation.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    client = self.context[constants.CLIENT]
    resources = self.context[constants.RESOURCES]
    operation_ref = resources.Parse(args.operation,
                                    collection=constants.OPERATIONS_COLLECTION)

    return client.operations.Get(operation_ref.Request())
