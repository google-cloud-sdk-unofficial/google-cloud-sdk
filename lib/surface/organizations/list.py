# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command to list all organization IDs associated with the active user."""


from googlecloudsdk.api_lib.cloudresourcemanager import organizations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.organizations import org_utils


class List(base.ListCommand):
  """List organizations accessible by the active account.

  Lists all organizations to which the active account has access. Organizations
  are listed in an unspecified order.

  The active account can be a user account or a service account. If the active
  account is a service account, then the list of organizations might be
  incomplete. Specifically, the list excludes organizations that the active
  account only has access to because they're in a [service account principal
  set](https://cloud.google.com/iam/help/service-accounts/principal-sets) with
  access to the organization.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        """
          table(
            displayName:label=DISPLAY_NAME,
            name.segment():label=ID:align=right:sort=1,
            owner.directoryCustomerId:label=DIRECTORY_CUSTOMER_ID:align=right
          )""")
    parser.display_info.AddUriFunc(org_utils.OrganizationsUriFunc)

  def Run(self, args):
    """Run the list command."""
    orgs_client = organizations.Client()
    return orgs_client.List(limit=args.limit, page_size=args.page_size)
