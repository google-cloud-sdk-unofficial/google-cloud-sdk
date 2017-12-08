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

"""service-management operations describe command."""

import sys

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


OPTIONAL_PREFIX_TO_STRIP = 'operations/'
MAX_RESPONSE_BYTES = 1000


class Describe(base.DescribeCommand, base_classes.BaseServiceManagementCommand):
  """Describes a service given a service name."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'operation', help='The name of the Operation to describe.')
    parser.add_argument(
        '--full',
        action='store_true',
        default=False,
        help=('Print the entire Operation resource, which could be large. '
              'By default, a summary will be printed instead.'))

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Run 'service-management operations describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the operations.Get API call.
    """
    # If a user includes the leading "operations/", just strip it off
    if args.operation.startswith(OPTIONAL_PREFIX_TO_STRIP):
      args.operation = args.operation[len(OPTIONAL_PREFIX_TO_STRIP):]

    request = self.services_messages.ServicemanagementOperationsGetRequest(
        operationsId=args.operation,
    )

    operation = self.services_client.operations.Get(request)

    if (sys.getsizeof(str(operation.response)) > MAX_RESPONSE_BYTES and
        not args.full):
      log.warn('Response portion of Operation redacted. '
               'Use --full to see the whole Operation.\n')
      operation.response = None

    # Set async to True because we don't need to wait for the operation
    # to complete to check the status of it.
    return services_util.GetProcessedOperationResult(operation, async=True)
