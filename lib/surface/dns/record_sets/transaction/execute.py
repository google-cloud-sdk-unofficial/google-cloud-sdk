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

"""gcloud dns record-sets transaction execute command."""

import os
from googlecloudsdk.api_lib.dns import import_util
from googlecloudsdk.api_lib.dns import transaction_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Execute(base.ListCommand):
  """Execute the transaction on Cloud DNS.

  This command executes the transaction on Cloud DNS. This will result in
  record-sets being changed as specified in the transaction.

  ## EXAMPLES

  To execute the transaction, run:

    $ {command} -z MANAGED_ZONE
  """

  @staticmethod
  def Args(parser):
    flags.GetZoneArg().AddToParser(parser)
    parser.display_info.AddFormat(flags.CHANGES_FORMAT)

  def Run(self, args):
    with transaction_util.TransactionFile(args.transaction_file) as trans_file:
      change = transaction_util.ChangeFromYamlFile(trans_file)

    if import_util.IsOnlySOAIncrement(change):
      log.status.Print(
          'Nothing to do, empty transaction [{0}]'.format(
              args.transaction_file))
      os.remove(args.transaction_file)
      return None

    dns = apis.GetClientInstance('dns', 'v1')
    messages = apis.GetMessagesModule('dns', 'v1')
    zone_ref = resources.REGISTRY.Parse(
        args.zone,
        params={
            'project': properties.VALUES.core.project.GetOrFail,
        },
        collection='dns.managedZones')

    # Send the change to the service.
    result = dns.changes.Create(messages.DnsChangesCreateRequest(
        change=change, managedZone=zone_ref.Name(), project=zone_ref.project))
    change_ref = resources.REGISTRY.Create(
        collection='dns.changes', project=zone_ref.project,
        managedZone=zone_ref.Name(), changeId=result.id)
    msg = 'Executed transaction [{0}] for managed-zone [{1}].'.format(
        args.transaction_file, zone_ref.Name())
    log.status.Print(msg)
    log.CreatedResource(change_ref)
    os.remove(args.transaction_file)
    return result
