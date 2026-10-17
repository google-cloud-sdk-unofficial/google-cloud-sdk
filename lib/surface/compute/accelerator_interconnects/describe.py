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
"""Command for describing accelerator interconnects."""

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
class Describe(base.DescribeCommand):
  """Describe a Compute Engine accelerator interconnect."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    compute_flags.AddZoneFlag(
        parser,
        resource_type='accelerator interconnect',
        operation_type='describe',
    )
    parser.add_argument(
        'name',
        metavar='NAME',
        help='Name of the accelerator interconnect to describe.',
    )

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

    request = util.MakeDescribeRequest(
        messages=messages,
        project=project,
        zone=zone,
        name=args.name,
    )

    service = client.apitools_client.acceleratorInterconnects
    method_name = 'Get'
    errors = []
    responses = client.MakeRequests(
        [(service, method_name, request)],
        errors_to_collect=errors,
    )
    if errors:
      raise core_exceptions.MultiError(errors)
    return responses[0] if responses else None


Describe.detailed_help = {
    'brief': 'Describe a Compute Engine accelerator interconnect.',
    'DESCRIPTION': (
        """
        *{command}* describes a Compute Engine accelerator interconnect and
        displays its details, status, and health.
        """
    ),
    'EXAMPLES': (
        """
        To display details of an accelerator interconnect named
        `my-interconnect` in zone `us-central1-a`:

          $ {command} my-interconnect --zone=us-central1-a
        """
    ),
}
