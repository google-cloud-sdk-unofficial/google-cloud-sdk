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
"""gcloud dns managed-zone create command."""

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class Create(base.CreateCommand):
  """Create a Cloud DNS managed-zone.

  This command creates a Cloud DNS managed-zone.

  ## EXAMPLES

  To create a managed-zone, run:

    $ {command} my_zone --dns-name my.zone.com. --description "My zone!"
  """

  @staticmethod
  def Args(parser):
    flags.GetDnsZoneArg(
        'The name of the managed-zone to be created.').AddToParser(parser)
    parser.add_argument(
        '--dns-name',
        required=True,
        help='The DNS name suffix that will be managed with the created zone.')
    parser.add_argument('--description',
                        required=True,
                        help='Short description for the managed-zone.')

  def Collection(self):
    return 'dns.managedZones'

  def Run(self, args):
    dns = apis.GetClientInstance('dns', 'v1')
    messages = apis.GetMessagesModule('dns', 'v1')

    zone_ref = resources.REGISTRY.Parse(
        args.dns_zone, collection='dns.managedZones')

    zone = messages.ManagedZone(name=zone_ref.managedZone,
                                dnsName=util.AppendTrailingDot(args.dns_name),
                                description=args.description)

    result = dns.managedZones.Create(
        messages.DnsManagedZonesCreateRequest(managedZone=zone,
                                              project=zone_ref.project))
    log.CreatedResource(zone_ref)
    return result
