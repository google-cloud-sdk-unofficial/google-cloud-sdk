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
"""Command for creating accelerator interconnects."""

from typing import Any

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.accelerator_interconnects import util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties


@base.UniverseCompatible
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.PREVIEW)
class Create(base.CreateCommand):
  """Create a Compute Engine accelerator interconnect."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    compute_flags.AddZoneFlag(
        parser,
        resource_type='accelerator interconnect',
        operation_type='create',
    )
    parser.add_argument(
        'name',
        metavar='NAME',
        help='The name of the accelerator interconnect to create.',
    )
    parser.add_argument(
        '--accelerator-topology',
        help=(
            'Target accelerator topology shape (e.g., "2x2x4", "4x4x8",'
            ' "4x4x16").'
        ),
    )

    pool_group = parser.add_group(mutex=True)
    pool_group.add_argument(
        '--partition-ids',
        type=arg_parsers.ArgList(),
        metavar='PARTITION_ID',
        help=(
            'List of physical topology block identifiers (e.g. partition IDs)'
            ' to form the capacity pool.'
        ),
    )
    pool_group.add_argument(
        '--capacity-pool',
        type=arg_parsers.ArgList(),
        metavar='RESOURCE_URI',
        help=(
            'List of fully-qualified or relative URIs of resources (instances,'
            ' MIGs, reservation subblocks) forming the capacity pool.'
        ),
    )

    parser.add_argument(
        '--description',
        help='An optional textual description of the accelerator interconnect.',
    )
    parser.add_argument(
        '--reactivation-mode',
        choices={
            'manual': (
                'The accelerator interconnect must be manually reactivated or'
                ' recreated upon capacity repair.'
            )
        },
        help='Reactivation mode for the accelerator interconnect.',
    )
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
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

    request = util.MakeCreateRequest(
        messages=messages,
        project=project,
        zone=zone,
        name=args.name,
        accelerator_topology=args.accelerator_topology,
        partition_ids=args.partition_ids,
        capacity_pool=args.capacity_pool,
        description=args.description,
        reactivation_mode=args.reactivation_mode,
        labels=args.labels,
    )

    service = client.apitools_client.acceleratorInterconnects
    method_name = 'Insert'
    requests = [(service, method_name, request)]

    if not args.async_:
      errors = []
      responses = client.MakeRequests(
          requests,
          errors_to_collect=errors,
      )
      if errors:
        raise core_exceptions.MultiError(errors)
      return responses

    errors_to_collect = []
    responses = client.AsyncRequests(requests, errors_to_collect)
    if errors_to_collect:
      raise core_exceptions.MultiError(errors_to_collect)
    return responses


Create.detailed_help = {
    'brief': 'Create a Compute Engine accelerator interconnect.',
    'DESCRIPTION': (
        """
        *{command}* creates a Compute Engine accelerator interconnect resource
        representing a dynamic accelerator slice.
        """
    ),
    'EXAMPLES': (
        """
        To create an accelerator interconnect named `my-interconnect` in zone
        `us-central1-a` with a `2x2x4` topology:

          $ {command} my-interconnect --zone=us-central1-a \\
              --accelerator-topology=2x2x4 --partition-ids=partition-1

        To create an accelerator interconnect using specific instance capacity:

          $ {command} my-interconnect --zone=us-central1-a \\
              --accelerator-topology=2x2x4 \\
              --capacity-pool=\\
          projects/my-proj/zones/us-central1-a/instances/vm-1,\\
          projects/my-proj/zones/us-central1-a/instances/vm-2
        """
    ),
}
