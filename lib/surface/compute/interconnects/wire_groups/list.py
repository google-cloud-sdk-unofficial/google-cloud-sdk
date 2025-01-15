# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Command for listing wire groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Any

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import filter_rewrite
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.interconnects.wire_groups import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projection_spec


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List wire groups."""

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat("""
        table(
          name,
          description,
          crossSiteNetwork,
          wireGroupProperties.type:label=TYPE,
          wireProperties.bandwidthUnmetered:label=BANDWIDTH_UNMETERED,
          wireProperties.bandwidthMetered:label=BANDWIDTH_METERED,
          wireProperties.networkServiceClass:label=NETWORK_SERVICE_CLASS,
          wireProperties.bandwidthAllocation:label=BANDWIDTH_ALLOCATION,
          wireProperties.faultResponse:label=FAULT_RESPONSE,
          adminEnabled:label=ADMIN_ENABLED
        )
    """)
    flags.AddCrossSiteNetwork(parser)

  def Run(self, args: Any):
    """Run the list command.

    Args:
      args: The arguments of the command.

    Returns:
      Result of wire groups list requests.
    """

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE

    project = properties.VALUES.core.project.GetOrFail()

    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases
    )
    args.filter, filter_expr = filter_rewrite.Rewriter().Rewrite(
        args.filter, defaults=defaults
    )
    request = messages.ComputeWireGroupsListRequest(
        project=project,
        crossSiteNetwork=args.cross_site_network,
        filter=filter_expr,
    )

    return list_pager.YieldFromList(
        client.wireGroups,
        request,
        field='items',
        limit=args.limit,
        batch_size=None,
    )


List.detailed_help = base_classes.GetGlobalListerHelp('wire groups')
