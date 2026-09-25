# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""'vmware capacity-allocations list' command."""

from typing import Any

from googlecloudsdk.api_lib.vmware import capacity_allocations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION': """
          List VMware Engine capacity allocations.
        """,
    'EXAMPLES': """
          To list VMware Engine capacity allocations in location `us-west1-a`, run:

            $ {command} --location=us-west1-a --project=my-project

          To list VMware Engine capacity allocations across all locations, run:

            $ {command} --location=-
    """,
}


# TODO(b/555788747): Add E2E tests for gcloud vmware capacity-allocations
# list command.
@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List VMware Engine capacity allocations."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    """Register flags for this command."""
    flags.AddLocationArgToParser(parser)
    parser.add_argument(
        '--connected-placement-group',
        help="""\
        Only show capacity allocations connected to the specified placement group.
        """,
    )
    parser.display_info.AddFormat("""
        table(
          name.basename():label=NAME,
          name.segment(-3):label=LOCATION,
          machineFamily:label=MACHINE_FAMILY,
          allocatedCapacityCount:label=ALLOCATED_NODES,
          consumedCapacityCount:label=CONSUMED_NODES,
          privateClouds.map().basename().list():label=PRIVATE_CLOUDS
        )
    """)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    location = args.CONCEPTS.location.Parse()
    filter_expr = args.filter
    if args.connected_placement_group:
      # 'connectedPlacementGroup' is a custom server-side filter parameter
      # evaluated by the backend API. It does not exist as a field on the
      # CapacityAllocation resource schema, so it cannot be evaluated
      # client-side via standard gcloud filtering.
      connected_filter = (
          f'connectedPlacementGroup="{args.connected_placement_group}"'
      )
      if filter_expr:
        filter_expr = f'({filter_expr}) AND ({connected_filter})'
      else:
        filter_expr = connected_filter

    client = capacity_allocations.CapacityAllocationsClient()
    return client.List(
        location,
        filter_expression=filter_expr,
        page_size=args.page_size,
        limit=args.limit,
    )
