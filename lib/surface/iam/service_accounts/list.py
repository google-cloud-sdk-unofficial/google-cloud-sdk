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
"""Command for to list all of a project's service accounts."""


from googlecloudsdk.api_lib.iam import base_classes
from googlecloudsdk.api_lib.iam import data_formats
from googlecloudsdk.api_lib.iam import utils
from googlecloudsdk.third_party.apitools.base.py import list_pager


class List(base_classes.BaseIamCommand):
  """List all of a project's service accounts."""

  @staticmethod
  def Args(parser):
    parser.add_argument('--limit',
                        type=int,
                        help='The maximum number of service accounts to '
                        'return.')

  @utils.CatchHttpErrors
  def Run(self, args):
    if args.limit is not None:
      if args.limit < 1:
        raise ValueError('Limit size must be >=1')

    # TODO(user): We can't use the default list printing functions until
    # there is support for atomic names. This property is the equivalent of
    # a COLUMN_MAP for the list printer. To be removed in the future.
    self.data_format = data_formats.SERVICE_ACCOUNT_COLUMNS
    return list_pager.YieldFromList(
        self.iam_client.projects_serviceAccounts,
        self.messages.IamProjectsServiceAccountsListRequest(
            name=utils.ProjectToProjectResourceName(self.project.Get())),
        field='accounts',
        limit=args.limit,
        batch_size_attribute='pageSize')
