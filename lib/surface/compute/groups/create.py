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
"""Command for creating groups."""
from googlecloudsdk.api_lib.compute import base_classes


class Create(base_classes.BaseAsyncCreator):
  """Create Google Compute Engine groups."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'names',
        metavar='NAME',
        nargs='+',
        help='The name of the group to create.')

    parser.add_argument(
        '--description',
        help='An optional, textual description for the group being created.')

  @property
  def service(self):
    return self.clouduseraccounts.groups

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'groups'

  @property
  def messages(self):
    return self.clouduseraccounts.MESSAGES_MODULE

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding users."""

    group_refs = [self.clouduseraccounts_resources.Parse(
        group, collection='clouduseraccounts.groups') for group in args.names]

    requests = []
    for group_ref in group_refs:

      group = self.messages.Group(
          name=group_ref.Name(),
          description=args.description,
      )

      request = self.messages.ClouduseraccountsGroupsInsertRequest(
          project=self.project,
          group=group)
      requests.append(request)

    return requests


Create.detailed_help = {
    'brief': 'Create Google Compute Engine groups',
    'DESCRIPTION': """\
        *{command}* creates Google Compute Engine groups.
        """,
    'EXAMPLES': """\
        To create a group, run:

          $ {command} example-group
        """,
}
