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

"""Command to get information about a principal's permissions on a service."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.third_party.apitools.base.py import exceptions as apitools_exceptions


class Check(base.Command, base_classes.AccessCommand):
  """Returns information about a principal's permissions on a service."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """

    parser.add_argument(
        '--service',
        required=True,
        help='The service for which to check the access policy.')
    parser.add_argument(
        'principal', help='The user email for which to check permissions.')

  def Run(self, args):
    """Run 'service-management access check'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the access API call.

    Raises:
      HttpException: An http error response was received while executing api
        request.
    """
    # Shorten the query request name for better readability
    query_request = (self.services_messages
                     .ServicemanagementServicesAccessPolicyQueryRequest)
    request = query_request(serviceName=args.service, userEmail=args.principal)

    try:
      return self.services_client.services_accessPolicy.Query(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(services_util.GetError(error))
