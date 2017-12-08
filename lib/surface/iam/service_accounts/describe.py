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
"""Command for getting service accounts."""


import textwrap

from apitools.base.py import exceptions

from googlecloudsdk.api_lib.iam import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import base_classes


class Describe(base_classes.BaseIamCommand, base.DescribeCommand):
  """Show metadata for a service account from a project."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          This command shows metadata for a service account.

          This call can fail for the following reasons:
              * The service account specified does not exist.
              * The active user does not have permission to access the given
                service account.
          """),
      'EXAMPLES': textwrap.dedent("""\
          To print metadata for a service account from your project, run:

            $ {command} my-iam-account@somedomain.com
          """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('account',
                        metavar='IAM-ACCOUNT',
                        help='The service account to describe.')

  def Run(self, args):
    try:
      # TODO(user): b/25212870
      # gcloud's resource support doesn't yet work for atomic names. When it
      # does this needs to be rewritten to use it.
      # ref = self.ParseServiceAccount(args.account)
      # return self.iam_client.projects_serviceAccounts.Get(ref.Request())
      return self.iam_client.projects_serviceAccounts.Get(
          self.messages.IamProjectsServiceAccountsGetRequest(
              name=utils.EmailToAccountResourceName(args.account)))
    except exceptions.HttpError as error:
      raise utils.ConvertToServiceAccountException(error, args.account)
