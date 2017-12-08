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

"""Command for adding a principal to a service's access policy."""

import httplib

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.api_lib.util import http_retry
from googlecloudsdk.calliope import base
from googlecloudsdk.core.iam import iam_util


class Add(base.Command, base_classes.BaseServiceManagementCommand):
  """Adds IAM policy binding to a service's access policy."""

  detailed_help = iam_util.GetDetailedHelpForAddIamPolicyBinding(
      'service', 'my-service')

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """

    parser.add_argument(
        'service',
        help='The service to which the member is to be added.')
    parser.add_argument(
        '--member', required=True,
        help='The member to add to the binding.')

  @http_error_handler.HandleHttpErrors
  @http_retry.RetryOnHttpStatus(httplib.CONFLICT)
  def Run(self, args):
    """Run 'service-management access add'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the access API call.

    Raises:
      ToolException: An error such as specifying a label that doesn't exist
        or a principal that is already a member of the service or visibility
        label.
    """
    request = (self.services_messages
               .ServicemanagementServicesGetIamPolicyRequest(
                   servicesId=args.service))

    try:
      policy = self.services_client.services.GetIamPolicy(request)
    except apitools_exceptions.HttpError as error:
      if http_error_handler.GetHttpErrorStatusCode(error) == 404:
        policy = self.services_messages.Policy()
      else:
        raise

    iam_util.AddBindingToIamPolicy(
        self.services_messages, policy, args.member,
        'roles/servicemanagement.serviceConsumer')

    # Send updated access policy to backend
    request = (self.services_messages
               .ServicemanagementServicesSetIamPolicyRequest(
                   servicesId=args.service,
                   setIamPolicyRequest=(self.services_messages.
                                        SetIamPolicyRequest(policy=policy))))
    return self.services_client.services.SetIamPolicy(request)
