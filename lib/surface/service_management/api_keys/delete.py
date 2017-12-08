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

"""Implementation of the service-management api-keys delete command."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base


class Delete(base.Command, base_classes.BaseServiceManagementCommand):
  """Deletes a key."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('--key',
                        '-k',
                        help='The identifier of the key to be deleted.')

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Run 'service-management api-keys delete'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the keys API call.
    """
    # Construct the Delete API Key request object
    request = self.apikeys_messages.ApikeysProjectsApiKeysDeleteRequest(
        projectId=self.project,
        keyId=args.key)

    result = self.apikeys_client.projects_apiKeys.Delete(request)

    # Note that we expect an empty proto as a result (google.protobuf.Empty).
    # If that's what we receive, we can assume success.
    return result or {'key': args.key, 'success': True}
