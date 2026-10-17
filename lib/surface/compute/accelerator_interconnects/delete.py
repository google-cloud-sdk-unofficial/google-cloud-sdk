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
"""Command for deleting accelerator interconnects."""

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
class Delete(base.DeleteCommand):
  """Delete a Compute Engine accelerator interconnect."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    compute_flags.AddZoneFlag(
        parser,
        resource_type='accelerator interconnect',
        operation_type='delete',
    )
    parser.add_argument(
        'name',
        metavar='NAME',
        help='Name of the accelerator interconnect to delete.',
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

    request = util.MakeDeleteRequest(
        messages=messages,
        project=project,
        zone=zone,
        name=args.name,
    )

    service = client.apitools_client.acceleratorInterconnects
    method_name = 'Delete'
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


Delete.detailed_help = {
    'brief': 'Delete a Compute Engine accelerator interconnect.',
    'DESCRIPTION': (
        """
        *{command}* deletes a Compute Engine accelerator interconnect resource,
        tearing down the dynamic interconnect network.
        """
    ),
    'EXAMPLES': (
        """
        To delete an accelerator interconnect named `my-interconnect` in zone
        `us-central1-a`:

          $ {command} my-interconnect --zone=us-central1-a
        """
    ),
}
