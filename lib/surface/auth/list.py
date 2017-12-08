# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Command to list the available accounts."""

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.resource import resource_printer


class _AuthInfo(object):

  def __init__(self, active_account, accounts):
    self.active_account = active_account
    self.accounts = accounts


class List(base.Command):
  """Lists credentialed accounts.

  Lists accounts whose credentials have been obtained using `gcloud init`,
  `gcloud auth login` and `gcloud auth activate-service-account`, and shows
  which account is active. The active account is used by gcloud and other Cloud
  SDK tools to access Google Cloud Platform.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument('--filter-account',
                        help='List only the specified account.')

  def Run(self, args):
    """List the account for known credentials."""
    accounts = c_store.AvailableAccounts()

    active_account = properties.VALUES.core.account.Get()

    if args.filter_account:
      if args.filter_account in accounts:
        accounts = [args.filter_account]
      else:
        accounts = []

    return _AuthInfo(active_account, accounts)

  def Display(self, unused_args, result):
    if result.accounts:
      items = [account +
               (' (active)' if account == result.active_account else '')
               for account in result.accounts]
      fmt = 'list[title="Credentialed accounts:"]'
      resource_printer.Print(items, fmt)
      log.err.Print(textwrap.dedent("""
          To set the active account, run:
            $ gcloud config set account `ACCOUNT`
          """))
    else:
      log.err.Print(textwrap.dedent("""\
          No credentialed accounts.

          To login, run:
            $ gcloud auth login `ACCOUNT`
          """))
