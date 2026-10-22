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
class QueryFormability(base.ListCommand):
  """Query formability for accelerator interconnects."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.URI_FLAG.RemoveFromParser(parser)
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
    parser.display_info.AddFormat("""
        table(
          partitionId:label=PARTITION_ID,
          acceleratorTopology:label=TOPOLOGY,
          status.state:label=STATE,
          status.infrastructureHealth:label=INFRA_HEALTH,
          status.instanceState:label=INSTANCE_STATE,
          status.usageState:label=USAGE_STATE,
          subblock.basename():label=SUBBLOCK,
          parent:label=PARENT,
          status.acceleratorInterconnect.basename():label=ACCELERATOR_INTERCONNECT:optional,
          status.instance.basename():label=INSTANCE:optional,
          status.error.message:label=ERROR:wrap:optional
        )
    """)
    parser.display_info.AddCacheUpdater(None)

  def Run(
      self, args: parser_extensions.Namespace
  ) -> list[util.PartitionFormabilityRecord]:
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

    results = util.TransformFormabilityResponse(response)
    for record in results:
      status = record.get('status')
      if isinstance(status, dict) and 'error' in status:
        error = status['error']
        message = (
            error.get('message') if isinstance(error, dict) else str(error)
        )
        subblock_name = record.get('subblock', '').split('/')[-1]
        log.warning(
            'Subblock [{0}] formability item error: {1}'.format(
                subblock_name, message or 'Evaluation failed'
            )
        )

    self._had_results = bool(results)
    if not results:
      log.status.Print('No partitions found for the specified subblocks.')
      return []

    return results

  def Epilog(self, resources_were_displayed: bool) -> None:
    if getattr(self, '_had_results', True):
      super().Epilog(resources_were_displayed)


QueryFormability.detailed_help = {
    'brief': 'Query formability for accelerator interconnects.',
    'DESCRIPTION': (
        """
        *{command}* queries hierarchical partition trees across dense
        reservation subblocks to determine physical topology health, instance
        lifecycle states, and placement formability for accelerator
        interconnects in a specified zone.
    """
    ),
    'EXAMPLES': (
        """
        To query formability for subblock `sb-1` in zone `us-central1-a`:

          $ {command} --zone=us-central1-a --subblocks=sb-1

        To query formability across multiple subblocks:

          $ {command} --zone=us-central1-a --subblocks=sb-1,sb-2

        To filter results by a specific accelerator topology shape
        (e.g., 4x4x4):

          $ {command} --zone=us-central1-a --subblocks=sb-1 \
              --filter="acceleratorTopology=4x4x4"
    """
    ),
}
