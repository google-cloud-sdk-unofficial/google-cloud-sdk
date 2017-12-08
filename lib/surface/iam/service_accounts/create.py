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
"""Command to create a service account for a project."""


import textwrap

from googlecloudsdk.api_lib.iam import utils
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.exceptions import InvalidArgumentException
from googlecloudsdk.command_lib.iam import base_classes
from googlecloudsdk.core import properties


class Create(base_classes.BaseIamCommand, base.CreateCommand):
  """Create an service account for a project.

  This command creates a service account with the provided name. For
  subsequent commands regarding service accounts, this service account should be
  referred to by the email account in the response.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': textwrap.dedent("""\
          To create an service account for your project, run:

            $ {command} some-account-name --display-name "My Service Account"

          To work with this service account in subsequent IAM commands, use the
          email resulting from this call as the IAM-ACCOUNT argument.
          """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('--display-name',
                        help='A textual name to display for the account.')

    parser.add_argument('name',
                        metavar='NAME',
                        help='The internal name of the new service account. '
                        'Used to generate an IAM-ACCOUNT (an IAM internal '
                        'email address used as an identifier of service '
                        'account), which must be passed to subsequent '
                        'commands.')

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    if not utils.ValidateAccountId(args.name):
      raise InvalidArgumentException(args.name, 'invalid name')

    project = properties.VALUES.core.project.Get(required=True)

    return self.iam_client.projects_serviceAccounts.Create(
        self.messages.IamProjectsServiceAccountsCreateRequest(
            name=utils.ProjectToProjectResourceName(project),
            createServiceAccountRequest=
            self.messages.CreateServiceAccountRequest(
                accountId=args.name,
                serviceAccount=self.messages.ServiceAccount(
                    displayName=args.display_name))))
