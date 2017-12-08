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
"""Command for getting IAM policies for service accounts."""


import textwrap

from apitools.base.py import exceptions

from googlecloudsdk.api_lib.iam import utils
from googlecloudsdk.command_lib.iam import base_classes


class GetIamPolicy(base_classes.BaseIamCommand):
  """Get the IAM policy for a service account."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': textwrap.dedent("""\
          To print the IAM policy for a given service account, run:

            $ {command} my-iam-account@somedomain.com
          """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('account',
                        metavar='IAM-ACCOUNT',
                        help='The service account whose policy to '
                        'get.')

  def Run(self, args):
    try:
      return self.iam_client.projects_serviceAccounts.GetIamPolicy(
          self.messages.IamProjectsServiceAccountsGetIamPolicyRequest(
              resource=utils.EmailToAccountResourceName(args.account)))
    except exceptions.HttpError as error:
      raise utils.ConvertToServiceAccountException(error, args.account)
