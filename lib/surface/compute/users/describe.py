# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for describing users."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute.users import utils as user_utils
from googlecloudsdk.command_lib.util import gaia


class Describe(base_classes.BaseAsyncMutator):
  """Describe a Google Compute Engine user.

  *{command}* displays all data associated with a Google Compute
  Engine user in a project.
  """

  @staticmethod
  def Args(parser):
    user_utils.AddUserArgument(parser, 'describe')

  @property
  def service(self):
    return self.clouduseraccounts.users

  @property
  def method(self):
    return 'Get'

  @property
  def resource_type(self):
    return 'users'

  @property
  def messages(self):
    return self.clouduseraccounts.MESSAGES_MODULE

  def CreateRequests(self, args):
    """Returns a list of requests necessary for describing users."""

    user = args.name
    if not user:
      user = gaia.GetDefaultAccountName(self.http)

    user_ref = self.clouduseraccounts_resources.Parse(
        user, collection='clouduseraccounts.users')

    request = self.messages.ClouduseraccountsUsersGetRequest(
        project=self.project,
        user=user_ref.Name())

    return [request]


Describe.detailed_help = {
    'EXAMPLES': """\
        To describe a user, run:

          $ {command} example-user

        To describe the default user mapped from the currently authenticated
        Google account email, run:

          $ {command}
        """,
}
