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

"""gcloud dns record-sets transaction remove command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.dns import transaction_util as trans_util
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Remove(base.Command):
  """Append a record-set deletion to the transaction.

  This command appends a record-set deletion to the transaction.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To remove an A record, run:

            $ {command} -z MANAGED_ZONE --name my.domain. --ttl 1234 --type A "1.2.3.4"

          To remove a TXT record with multiple data values, run:

            $ {command} -z MANAGED_ZONE --name my.domain. --ttl 2345 --type TXT "Hello world" "Bye world"
          """,
  }

  @staticmethod
  def Args(parser):
    util.ZONE_FLAG.AddToParser(parser)
    parser.add_argument(
        '--name', required=True,
        help='DNS name of the record-set to be removed.')
    parser.add_argument(
        '--ttl', required=True, type=int,
        help='TTL for the record-set to be removed.')
    parser.add_argument(
        '--type', required=True,
        help='Type of the record-set to be removed.')
    parser.add_argument(
        'data', nargs='+',
        help='DNS name of the record-set to be removed.')

  @util.HandleHttpError
  def Run(self, args):
    with trans_util.TransactionFile(args.transaction_file) as trans_file:
      change = trans_util.ChangeFromYamlFile(trans_file)

    dns = self.context['dns_client']
    messages = self.context['dns_messages']
    resources = self.context['dns_resources']
    project_id = properties.VALUES.core.project.Get(required=True)

    record_to_remove = trans_util.CreateRecordSetFromArgs(args)

    # Ensure the record to be removed exists
    zone_ref = resources.Parse(args.zone, collection='dns.managedZones')
    existing_records = [record for record in list_pager.YieldFromList(
        dns.resourceRecordSets,
        messages.DnsResourceRecordSetsListRequest(
            project=project_id,
            managedZone=zone_ref.Name(),
            name=args.name,
            type=args.type),
        field='rrsets')]
    if not existing_records or existing_records[0] != record_to_remove:
      raise exceptions.ToolException('Record to be removed does not exist')

    change.deletions.append(record_to_remove)

    with trans_util.TransactionFile(args.transaction_file, 'w') as trans_file:
      trans_util.WriteToYamlFile(trans_file, change)

    log.status.Print(
        'Record removal appended to transaction at [{0}].'.format(
            args.transaction_file))
