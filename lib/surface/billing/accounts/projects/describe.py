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

"""Command to show metadata for a specified project."""

import textwrap
from googlecloudsdk.api_lib.billing import utils
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """Show detailed billing information for a project."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent(
          """
          This command shows billing info for a project, given it's ID.

          This call can fail for the following reasons:
          * The project specified does not exist.
          * The active user does not have permission to access the given
          project.
          """
      ),
      'EXAMPLES': textwrap.dedent(
          """
          *{command}* 0X0X0X-0X0X0X-0X0X0X will print the info for
          billing account 0X0X0X-0X0X0X-0X0X0X.
          """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('project_id', **utils.PROJECT_ID_ARG_PARAMS)

  def Run(self, args):
    client = self.context['billing_client']
    messages = self.context['billing_messages']
    return client.projects.GetBillingInfo(
        messages.CloudbillingProjectsGetBillingInfoRequest(
            name='projects/{project_id}'.format(
                project_id=args.project_id,
            ),
        )
    )
