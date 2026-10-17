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
"""Command for listing accelerator interconnects."""

from typing import Any

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.accelerator_interconnects import util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties


@base.UniverseCompatible
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.PREVIEW)
class List(base.ListCommand):
  """List Compute Engine accelerator interconnects."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    compute_flags.AddZoneFlag(
        parser,
        resource_type='accelerator interconnects',
        operation_type='list',
    )
    parser.add_argument(
        '--zones',
        metavar='ZONE',
        help=(
            'Zone of the accelerator interconnects to list (alias for --zone).'
        ),
    )
    parser.display_info.AddFormat("""
        table(
          name,
          zone.basename(),
          acceleratorTopology:label=TOPOLOGY,
          status.state:label=STATE,
          status.acceleratorType:label=ACCELERATOR_TYPE
        )
    """)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    zone = getattr(args, 'zone', None) or getattr(args, 'zones', None)
    if not zone:
      zone = properties.VALUES.compute.zone.Get(required=True)
    args.zone = zone

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

    request = util.MakeListRequest(
        messages=messages,
        project=project,
        zone=zone,
    )

    service = client.apitools_client.acceleratorInterconnects
    method_name = 'List'
    errors = []
    responses = client.MakeRequests(
        [(service, method_name, request)],
        errors_to_collect=errors,
    )
    if errors:
      raise core_exceptions.MultiError(errors)
    return util.ExtractAcceleratorInterconnects(responses)


List.detailed_help = {
    'brief': 'List Compute Engine accelerator interconnects.',
    'DESCRIPTION': (
        """
        *{command}* lists Compute Engine accelerator interconnects in a given
        project and zone.
        """
    ),
    'EXAMPLES': (
        """
        To list all accelerator interconnects in zone `us-central1-a`:

          $ {command} --zone=us-central1-a
        """
    ),
}
