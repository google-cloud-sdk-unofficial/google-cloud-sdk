# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""'vmware private-clouds management-dns-zone-bindings create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.managementdnszonebinding import ManagementDNSZoneBindingClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a management DNS zone binding.
        """,
    'EXAMPLES':
        """
          To create a management DNS zone binding called `my-mgmt-dns-zone-binding` that corresponds to the vmware engine network `sample-vmware-engine-network` in private cloud
          `my-private-cloud`, in location `us-east2-b`, run:

            $ {command} my-mgmt-dns-zone-binding --project=my-project --private-cloud=my-private-cloud --location=us-east2-b --vmware-engine-network=sample-vmware-engine-network

          Or:

            $ {command} my-mgmt-dns-zone-binding --private-cloud=my-private-cloud --vmware-engine-network=sample-vmware-engine-network

          In the second example, the project and region are taken from gcloud properties `core/project` and `vmware/region`.
    """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a management DNS zone binding."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddManagementDnsZoneBindingArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--vpc-network',
        required=False,
        help="""\
        Resource name of the Google Cloud VPC network to bind to the management DNS zone of the  private cloud.
        """)
    group.add_argument(
        '--vmware-engine-network',
        required=False,
        help="""\
        Resource name of VMware Engine network to bind to the management DNS zone of the  private cloud.
        """)
    parser.add_argument(
        '--description',
        help="""\
        Text describing the binding resource that represents the network getting bound to the management DNS zone.
        """)

  def Run(self, args):
    mdzb = args.CONCEPTS.management_dns_zone_binding.Parse()
    client = ManagementDNSZoneBindingClient()
    is_async = args.async_
    operation = client.Create(mdzb, args.vpc_network,
                              args.vmware_engine_network, args.description)
    if is_async:
      log.CreatedResource(
          operation.name, kind='management DNS zone binding', is_async=True)
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=('waiting for management DNS zone binding [{}] ' +
                 'to be created').format(mdzb.RelativeName()))
    log.CreatedResource(resource, kind='management DNS zone binding')

    return resource