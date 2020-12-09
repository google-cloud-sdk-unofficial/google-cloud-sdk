# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""gcloud dns record-sets create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import resource_record_sets as rrsets_util
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create a record-set in a managed-zone.

  This command creates a record-set contained within the specified
  managed-zone.

  ## EXAMPLES

  To create a record-set with dnsName foo.bar.com., record type A, rrdata
  [1.2.3.4, 9.8.7.6] and ttl 60 in my_zone run this:

    $ {command} foo.bar.com. --rrdatas=1.2.3.4,9.8.7.6 --type=A --ttl=60
      --zone=my_zone

  """

  @staticmethod
  def Args(parser):
    flags.GetZoneArg().AddToParser(parser)
    flags.GetResourceRecordSetsNameArg().AddToParser(parser)
    flags.GetResourceRecordSetsTypeArg(True).AddToParser(parser)
    flags.GetResourceRecordSetsTtlArg(False).AddToParser(parser)
    flags.GetResourceRecordSetsRrdatasArg(True).AddToParser(parser)
    parser.display_info.AddCacheUpdater(None)
    parser.display_info.AddFormat(flags.RESOURCERECORDSETS_FORMAT)

  def Run(self, args):
    api_version = 'v1beta2'
    messages = apis.GetMessagesModule('dns', api_version)

    dns_client = util.GetApiClient(api_version)

    zone_ref = util.GetRegistry(api_version).Parse(
        args.zone,
        params={
            'project': properties.VALUES.core.project.GetOrFail,
        },
        collection='dns.managedZones')

    result = dns_client.resourceRecordSets.Create(
        messages.DnsResourceRecordSetsCreateRequest(
            project=zone_ref.project,
            managedZone=zone_ref.Name(),
            resourceRecordSet=rrsets_util.CreateRecordSetFromArgs(
                args, api_version)))

    return result
