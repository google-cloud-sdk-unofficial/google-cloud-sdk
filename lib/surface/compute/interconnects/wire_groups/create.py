# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command for creating wire groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects.wire_groups import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.interconnects.cross_site_networks import flags as cross_site_network_flags
from googlecloudsdk.command_lib.compute.interconnects.wire_groups import flags
from googlecloudsdk.core import properties


DETAILED_HELP = {
    'DESCRIPTION': """\
        *{command}* is used to create wire groups. A wire group represents a
        group of redundant wires between interconnects in two different metros.
        Each WireGroup belongs to a CrossSiteNetwork.

        For an example, refer to the *EXAMPLES* section below.
        """,
    'EXAMPLES': """\
        To create a wire group, run:

          $ {command} example-wire-group \
              --project my-project \
              --cross-site-network example-cross-site-network \
              --type WIRE \
              --bandwidth-unmetered 10g \
              --network-service-class BRONZE \
              --bandwidth-allocation ALLOCATE_PER_WIRE
        """,
}


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Compute Engine wire group.

  *{command}* is used to create wire groups. A wire group represents a
  group of redundant wires between interconnects in two different metros.
  Each WireGroup belongs to a CrossSiteNetwork.
  """

  WIRE_GROUP_ARG = None
  CROSS_SITE_NETWORK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.WIRE_GROUP_ARG = flags.WireGroupArgument(plural=False)
    cls.WIRE_GROUP_ARG.AddArgument(parser, operation_type='create')
    cls.CROSS_SITE_NETWORK_ARG = (
        cross_site_network_flags.CrossSiteNetworkArgumentForOtherResource()
    )
    cls.CROSS_SITE_NETWORK_ARG.AddArgument(parser)
    flags.AddDescription(parser)
    flags.AddType(parser)
    flags.AddBandwidthUnmetered(parser)
    flags.AddBandwidthMetered(parser)
    flags.AddFaultResponse(parser)
    flags.AddAdminEnabled(parser)
    flags.AddNetworkServiceClass(parser)
    flags.AddBandwidthAllocation(parser)
    flags.AddValidateOnly(parser)

  def Collection(self):
    return 'compute.wireGroups'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.WIRE_GROUP_ARG.ResolveAsResource(args, holder.resources)
    cross_site_network_ref = self.CROSS_SITE_NETWORK_ARG.ResolveAsResource(
        args, holder.resources
    )

    project = properties.VALUES.core.project.GetOrFail()
    wire_group = client.WireGroup(
        ref,
        project,
        compute_client=holder.client
    )

    return wire_group.Create(
        description=args.description,
        cross_site_network=cross_site_network_ref.SelfLink(),
        # Need to rename type as it conflicts with python built in type()
        wire_group_type=args.type,
        bandwidth_unmetered=args.bandwidth_unmetered,
        bandwidth_metered=args.bandwidth_metered,
        fault_response=args.fault_response,
        admin_enabled=args.admin_enabled,
        network_service_class=args.network_service_class,
        bandwidth_allocation=args.bandwidth_allocation,
        validate_only=args.validate_only,
    )


Create.detailed_help = DETAILED_HELP
