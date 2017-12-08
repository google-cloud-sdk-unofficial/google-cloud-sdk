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
"""Command for adding a user to a group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers


class AddMembers(base_classes.NoOutputAsyncMutator):
  """Add a user to a Google Compute Engine group.

  *{command}* adds a users to a Google Compute Engine group.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'names',
        metavar='NAME',
        nargs='+',
        help='The names of the groups to add members to.')

    parser.add_argument(
        '--members',
        metavar='USERNAME',
        required=True,
        type=arg_parsers.ArgList(min_length=1),
        help='The names or fully-qualified URLs of the users to add.')

  @property
  def service(self):
    return self.clouduseraccounts.groups

  @property
  def method(self):
    return 'AddMember'

  @property
  def resource_type(self):
    return 'groups'

  @property
  def messages(self):
    return self.clouduseraccounts.MESSAGES_MODULE

  def CreateRequests(self, args):
    user_refs = [self.clouduseraccounts_resources.Parse(
        user, collection='clouduseraccounts.users') for user in args.members]

    group_refs = [self.clouduseraccounts_resources.Parse(
        group, collection='clouduseraccounts.groups') for group in args.names]

    user_selflinks = [user_ref.SelfLink() for user_ref in user_refs]
    requests = []
    for group_ref in group_refs:
      new_member = self.messages.GroupsAddMemberRequest(
          users=user_selflinks)

      request = self.messages.ClouduseraccountsGroupsAddMemberRequest(
          project=self.project,
          groupsAddMemberRequest=new_member,
          groupName=group_ref.Name())
      requests.append(request)

    return requests


AddMembers.detailed_help = {
    'EXAMPLES': """\
        To add a user to a group, run:

          $ {command} example-group --members example-user

        To add multiple users to multiple groups, run:

          $ {command} example-group-1 example-group-2 --members example-user-1,example-user-2
        """,
}
