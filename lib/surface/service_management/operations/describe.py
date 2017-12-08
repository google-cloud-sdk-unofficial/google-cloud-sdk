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

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.third_party.apitools.base.py import exceptions as apitools_exceptions

OPTIONAL_PREFIX_TO_STRIP = 'operations/'


class Describe(base.Command, base_classes.BaseServiceManagementCommand):
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
        help=('Print the entire Operation resource, which could be large.'
              'Otherwise, a summary will be printed instead.'))

  def Run(self, args):
    """Run 'service-management operations describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the operations.Get API call.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    # If a user includes the leading "operations/", just strip it off
    if args.operation.startswith(OPTIONAL_PREFIX_TO_STRIP):
      args.operation = args.operation[len(OPTIONAL_PREFIX_TO_STRIP):]

    request = self.services_messages.ServicemanagementOperationsGetRequest(
        operationsId=args.operation,
    )

    try:
      result = self.services_client.operations.Get(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(services_util.GetError(error))

    if not args.full:
      log.warn('Response portion of Operation redacted. '
               'Use --full to see the whole Operation.\n')
      result.response = None

    return services_util.ProcessOperationResult(result)
