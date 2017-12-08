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
"""Command for reserving IP addresses."""


from googlecloudsdk.api_lib.iam import base_classes
from googlecloudsdk.api_lib.iam import utils
from googlecloudsdk.core import log


class Create(base_classes.BaseIamCommand):
  """Create Service Account."""

  @staticmethod
  def Args(parser):
    parser.add_argument('--display-name',
                        help='A textual name to display for the account.')

    parser.add_argument('--description',
                        help='A textual description for the account.')

    parser.add_argument('name',
                        metavar='NAME',
                        help='The internal name of the new service account. '
                        'Used to generate an IAM-ADDRESS, which must be passed '
                        'to subsequent commands.')

  @utils.CatchHttpErrors
  def Run(self, args):
    if not utils.ValidateAccountId(args.name):
      raise ValueError('[{0}] is an invalid name'.format(args.name))

    if not self.project or not self.project.Get():
      log.error('no project id set')
      return

    return self.iam_client.projects_serviceAccounts.Create(
        self.messages.IamProjectsServiceAccountsCreateRequest(
            name=utils.ProjectToProjectResourceName(self.project.Get()),
            createServiceAccountRequest=
            self.messages.CreateServiceAccountRequest(
                accountId=args.name,
                serviceAccount=self.messages.ServiceAccount(
                    displayName=args.display_name,
                    description=args.description))))
