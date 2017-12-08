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
"""Command for deleting groups."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils


class Delete(base_classes.BaseAsyncMutator):
  """Delete Google Compute Engine groups."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'names',
        metavar='NAME',
        nargs='+',
        help='The names of the groups to delete.')

  @property
  def service(self):
    return self.clouduseraccounts.groups

  @property
  def method(self):
    return 'Delete'

  @property
  def resource_type(self):
    return 'groups'

  @property
  def messages(self):
    return self.clouduseraccounts.MESSAGES_MODULE

  def CreateRequests(self, args):
    group_refs = [self.clouduseraccounts_resources.Parse(
        group, collection='clouduseraccounts.groups') for group in args.names]

    utils.PromptForDeletion(group_refs)

    requests = []
    for group_ref in group_refs:
      request = self.messages.ClouduseraccountsGroupsDeleteRequest(
          project=self.project,
          groupName=group_ref.Name())
      requests.append(request)

    return requests

Delete.detailed_help = {
    'brief': 'Delete Google Compute Engine groups',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine groups.
        """,
    'EXAMPLES': """\
        To delete a group, run:

          $ {command} example-group

        To delete multiple groups, run:

          $ {command} example-group-1 example-group-2
        """,
}
