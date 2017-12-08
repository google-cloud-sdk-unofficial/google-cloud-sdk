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

"""gcloud dns managed-zone delete command."""

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class Delete(base.Command):
  """Delete an empty Cloud DNS managed-zone.

  This command deletes an empty Cloud DNS managed-zone. An empty managed-zone
  has only SOA and NS record-sets.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To delete an empty managed-zone, run:

            $ {command} my_zone
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('dns_zone', metavar='ZONE_NAME',
                        completion_resource='dns.managedZones',
                        help='Name of the empty managed-zone to be deleted.')

  @util.HandleHttpError
  def Run(self, args):
    dns = self.context['dns_client']
    messages = self.context['dns_messages']
    resources = self.context['dns_resources']

    zone_ref = resources.Parse(args.dns_zone, collection='dns.managedZones')

    result = dns.managedZones.Delete(
        messages.DnsManagedZonesDeleteRequest(
            managedZone=zone_ref.managedZone,
            project=zone_ref.project))
    log.DeletedResource(zone_ref)
    return result
