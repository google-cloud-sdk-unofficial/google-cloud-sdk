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
"""Command to list all Project IDs linked with a billing account."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.billing import utils
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List all active projects associated with the specified billing account.

  *{command}* ACCOUNT_ID -- lists all active projects, for the specified
  billing account id.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument('id', **utils.ACCOUNT_ID_ARG_PARAMS)
    base.URI_FLAG.RemoveFromParser(parser)

  def Collection(self):
    return 'cloudbilling.projectBillingInfo'

  @staticmethod
  def GetUriCacheUpdateOp():
    """No resource URIs."""
    return None

  def Run(self, args):
    """Run the list command."""

    billing_client = self.context['billing_client']
    messages = self.context['billing_messages']

    return list_pager.YieldFromList(
        billing_client.billingAccounts_projects,
        messages.CloudbillingBillingAccountsProjectsListRequest(
            name='billingAccounts/{account_id}'.format(
                account_id=args.id,
            ),
        ),
        field='projectBillingInfo',
        batch_size_attribute='pageSize',
        limit=args.limit,
        predicate=args.filter
    )
