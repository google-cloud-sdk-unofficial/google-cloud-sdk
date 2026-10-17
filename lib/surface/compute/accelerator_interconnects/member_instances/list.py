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
"""Command for listing member instances of an accelerator interconnect."""

import typing

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
  """List member VM instances of an accelerator interconnect."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    compute_flags.AddZoneFlag(
        parser,
        resource_type='accelerator interconnect',
        operation_type='list',
    )
    parser.add_argument(
        '--accelerator-interconnect',
        required=True,
        help=(
            'Name of the accelerator interconnect to list member instances'
            ' for.'
        ),
    )

    parser.display_info.AddFormat("""
        table(
          instance.basename():label=INSTANCE,
          firstof(zone, instance.scope().segment(0)):label=ZONE,
          firstof(instance_id, instanceId, id):label=ID
        )
    """)
    parser.display_info.AddUriFunc(util.GetMemberInstanceUri)
    parser.display_info.AddCacheUpdater(None)

  def Run(
      self, args: parser_extensions.Namespace
  ) -> typing.List[util.MemberInstanceRecord]:
    interconnect_name = args.accelerator_interconnect

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages
    resources = holder.resources

    project = properties.VALUES.core.project.GetOrFail()
    zone = getattr(args, 'zone', None)

    if interconnect_name.startswith('http') or 'projects/' in interconnect_name:
      interconnect_ref = resources.Parse(
          interconnect_name,
          params={'project': project, 'zone': zone or ''},
          collection='compute.acceleratorInterconnects',
      )
      project = interconnect_ref.project
      zone = interconnect_ref.zone
      interconnect_name = interconnect_ref.Name()
    else:
      if not zone:
        zone = properties.VALUES.compute.zone.Get(required=True)
      zone_ref = resources.Parse(
          zone,
          params={'project': project},
          collection='compute.zones',
      )
      project = zone_ref.project
      zone = zone_ref.zone

    request = util.MakeMemberInstancesListRequest(
        messages=messages,
        project=project,
        zone=zone,
        interconnect_name=interconnect_name,
    )

    service = client.apitools_client.acceleratorInterconnectMemberInstances
    method_name = 'List'

    errors = []
    responses = client.MakeRequests(
        [(service, method_name, request)],
        errors_to_collect=errors,
    )
    if errors:
      raise core_exceptions.MultiError(errors)

    return util.FormatMemberInstances(responses, zone=zone)


List.detailed_help = {
    'brief': 'List member VM instances of an accelerator interconnect.',
    'DESCRIPTION': (
        """
        *{command}* lists the member VM instances participating in a specified
        accelerator interconnect.
    """
    ),
    'EXAMPLES': (
        """
        To list member VM instances of accelerator interconnect
        `my-interconnect` in zone `us-central1-a`:

          $ {command} --accelerator-interconnect=my-interconnect \\
              --zone=us-central1-a
    """
    ),
}
