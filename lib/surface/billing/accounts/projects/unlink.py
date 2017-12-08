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
"""Command to disable billing."""

import textwrap
from googlecloudsdk.api_lib.billing import utils
from googlecloudsdk.calliope import base


class Unlink(base.Command):
  """Unlink the account (if any) linked with a project."""
  detailed_help = {
      'DESCRIPTION': textwrap.dedent(
          """
          This command unlinks a project from it's linked billing
          account. This disables billing on the project.
          """
      )
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('project_id', **utils.PROJECT_ID_ARG_PARAMS)

  def Run(self, args):
    billing = self.context['billing_client']
    messages = self.context['billing_messages']

    result = billing.projects.UpdateBillingInfo(
        messages.CloudbillingProjectsUpdateBillingInfoRequest(
            name='projects/{project_id}'.format(
                project_id=args.project_id,
            ),
            projectBillingInfo=messages.ProjectBillingInfo(
                billingAccountName='',
            ),
        )
    )
    return result
