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

"""Command to update a new project."""

import textwrap
from googlecloudsdk.api_lib.billing import utils
from googlecloudsdk.calliope import base


class Link(base.Command):
  """Link a project with a billing account."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent(
          """\
          This command links a billing account to a project.
          If the specified billing account is open, this has
          the effect of enabling billing on the project.
          """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--account-id',
        dest='accountId',
        required=True,
        **utils.ACCOUNT_ID_ARG_PARAMS
    )
    parser.add_argument('projectId', **utils.PROJECT_ID_ARG_PARAMS)

  def Run(self, args):
    billing = self.context['billing_client']
    messages = self.context['billing_messages']

    result = billing.projects.UpdateBillingInfo(
        messages.CloudbillingProjectsUpdateBillingInfoRequest(
            name='projects/{project_id}'.format(
                project_id=args.projectId,
            ),
            projectBillingInfo=messages.ProjectBillingInfo(
                billingAccountName='billingAccounts/{account_id}'.format(
                    account_id=args.accountId,
                )
            )
        )
    )
    return result
