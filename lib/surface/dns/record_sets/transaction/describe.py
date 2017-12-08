# Copyright 2014 Google Inc. All Rights Reserved.
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

"""gcloud dns record-sets transaction describe command."""

from googlecloudsdk.api_lib.dns import transaction_util
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """Describe the transaction.

  This command displays the contents of the transaction.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To look at the contents of the transaction, run:

            $ {command} -z MANAGED_ZONE
          """,
  }

  @staticmethod
  def Args(parser):
    util.ZONE_FLAG.AddToParser(parser)

  def Run(self, args):
    with transaction_util.TransactionFile(args.transaction_file) as trans_file:
      return transaction_util.ChangeFromYamlFile(trans_file)
