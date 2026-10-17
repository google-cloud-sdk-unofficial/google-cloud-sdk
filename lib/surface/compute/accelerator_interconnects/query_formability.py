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
"""Command to query formability for accelerator interconnects."""

from typing import List

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.accelerator_interconnects import util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.UniverseCompatible
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.PREVIEW)
class QueryFormability(base.Command):
  """Query formability for accelerator interconnects."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    compute_flags.AddZoneFlag(
        parser,
        resource_type='accelerator interconnect',
        operation_type='query formability',
    )
    parser.add_argument(
        '--subblocks',
        type=arg_parsers.ArgList(min_length=1),
        metavar='SUBBLOCK',
        required=True,
        help='List of reservation subblock names or resource URLs to evaluate.',
    )
    parser.add_argument(
        '--topology',
        type=arg_parsers.RegexpValidator(
            r'^\d+x\d+x\d+$',
            'Topology shape must be in the format NxNxN (e.g. 2x2x4, 4x4x4).',
        ),
        metavar='TOPOLOGY',
        help=(
            'Filter results to partitions matching the specified accelerator'
            ' topology shape.'
        ),
    )
    parser.display_info.AddFormat("""
        table(
          partitionId:label=PARTITION_ID,
          acceleratorTopology:label=TOPOLOGY,
          state:label=STATE,
          infrastructureHealth:label=INFRA_HEALTH,
          instanceState:label=INSTANCE_STATE,
          usageState:label=USAGE_STATE,
          subblock:label=SUBBLOCK,
          parent:label=PARENT
        )
    """)

  def Run(
      self, args: parser_extensions.Namespace
  ) -> List[util.PartitionFormabilityRecord]:
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    if not getattr(args, 'zone', None):
      args.zone = properties.VALUES.compute.zone.Get(required=True)

    project = properties.VALUES.core.project.GetOrFail()
    zone = args.zone

    if holder.resources:
      zone_ref = holder.resources.Parse(
          zone,
          params={'project': project},
          collection='compute.zones',
      )
      project = zone_ref.project
      zone = zone_ref.zone

    subblocks = util.ParseSubblocks(args.subblocks)

    request = util.MakeQueryFormabilityRequest(
        messages=messages,
        project=project,
        zone=zone,
        subblocks=subblocks,
    )

    service = client.apitools_client.acceleratorInterconnects
    method_name = 'QueryFormability'

    errors = []
    responses = client.MakeRequests(
        [(service, method_name, request)],
        errors_to_collect=errors,
    )
    if errors:
      raise core_exceptions.MultiError(errors)
    response = responses[0] if responses else None

    results = util.TransformFormabilityResponse(response, args.topology)
    if not results:
      if args.topology:
        log.status.Print(
            'No partitions found matching topology [{0}].'.format(args.topology)
        )
      else:
        log.status.Print('No partitions found for the specified subblocks.')
      return []

    return results


QueryFormability.detailed_help = {
    'brief': 'Query formability for accelerator interconnects.',
    'DESCRIPTION': """
        *{command}* queries hierarchical partition trees across dense
        reservation subblocks to determine physical topology health, instance
        lifecycle states, and placement formability for accelerator
        interconnects in a specified zone.
    """,
    'EXAMPLES': """
        To query formability for subblock `sb-1` in zone `us-central1-a`:

          $ {command} --zone=us-central1-a --subblocks=sb-1

        To query formability across multiple subblocks:

          $ {command} --zone=us-central1-a --subblocks=sb-1,sb-2

        To filter results by a specific accelerator topology shape
        (e.g., 4x4x4):

          $ {command} --zone=us-central1-a --subblocks=sb-1 --topology=4x4x4
    """,
}
