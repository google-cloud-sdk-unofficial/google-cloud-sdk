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
"""Command for describing groups."""
from googlecloudsdk.api_lib.compute import base_classes


class Describe(base_classes.BaseAsyncMutator):
  """Describe a Google Compute Engine group.

  *{command}* displays all data associated with a Google Compute
  Engine group in a project.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'name',
        metavar='NAME',
        help='The name of the group to describe.')

  @property
  def service(self):
    return self.clouduseraccounts.groups

  @property
  def method(self):
    return 'Get'

  @property
  def resource_type(self):
    return 'groups'

  @property
  def messages(self):
    return self.clouduseraccounts.MESSAGES_MODULE

  def CreateRequests(self, args):
    """Returns a list of requests necessary for describing groups."""

    group_ref = self.clouduseraccounts_resources.Parse(
        args.name, collection='clouduseraccounts.groups')

    request = self.messages.ClouduseraccountsGroupsGetRequest(
        project=self.project,
        groupName=group_ref.Name())

    return [request]


Describe.detailed_help = {
    'EXAMPLES': """\
        To describe a user, run:

          $ {command} example-user
        """,
}
