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


from googlecloudsdk.api_lib.iam import base_classes
from googlecloudsdk.api_lib.iam import utils


class Describe(base_classes.BaseIamCommand):
  """Describe Service Account."""

  @staticmethod
  def Args(parser):
    parser.add_argument('address',
                        metavar='IAM-ADDRESS',
                        help='The IAM service account address to describe.')

  @utils.CatchServiceAccountErrors
  def Run(self, args):
    self.SetAddress(args.address)
    # TODO(user): b/25212870
    # gcloud's resource support doesn't yet work for atomic names. When it does
    # this needs to be rewritten to use it.
    # ref = self.ParseServiceAccount(args.address)
    # return self.iam_client.projects_serviceAccounts.Get(ref.Request())
    return self.iam_client.projects_serviceAccounts.Get(
        self.messages.IamProjectsServiceAccountsGetRequest(
            name=utils.EmailToAccountResourceName(args.address)))
