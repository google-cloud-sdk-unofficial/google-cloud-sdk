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

"""Command to remove a principal from a service's access policy."""

import httplib

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.api_lib.util import http_retry
from googlecloudsdk.calliope import base
from googlecloudsdk.core.iam import iam_util


class Remove(base.Command, base_classes.BaseServiceManagementCommand):
  """Removes an IAM policy binding from a service's access policy."""

  detailed_help = iam_util.GetDetailedHelpForRemoveIamPolicyBinding(
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
        help='The service from which the member is to be removed.')
    parser.add_argument(
        '--member', required=True,
        help='The member to remove from the binding.')

  @http_error_handler.HandleHttpErrors
  @http_retry.RetryOnHttpStatus(httplib.CONFLICT)
  def Run(self, args):
    """Run 'service-management access remove'.

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

    policy = self.services_client.services.GetIamPolicy(request)

    iam_util.RemoveBindingFromIamPolicy(
        policy, args.member, 'roles/servicemanagement.serviceConsumer')

    # Send updated access policy to backend
    request = (self.services_messages
               .ServicemanagementServicesSetIamPolicyRequest(
                   servicesId=args.service,
                   setIamPolicyRequest=(self.services_messages.
                                        SetIamPolicyRequest(policy=policy))))
    return self.services_client.services.SetIamPolicy(request)
