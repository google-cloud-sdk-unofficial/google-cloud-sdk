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
"""Command for getting SBOM versions of a host in a reservation."""

import argparse
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.hosts import get_version_helper


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class GetVersion(base.Command):
  """Get software versions for a Compute Engine host in a reservation."""

  HOST_ARG = None

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser):
    """Set up arguments for this command."""
    cls.HOST_ARG = flags.ResourceArgument(
        resource_name='host',
        name='HOST_NAME',
        zonal_collection='compute.hosts',
        zone_explanation=flags.ZONE_PROPERTY_EXPLANATION,
    )
    cls.HOST_ARG.AddArgument(parser, operation_type='get version setting for')

    parser.add_argument(
        '--reservation',
        required=False,
        help='Name of the reservation the host is associated with.',
    )
    parser.add_argument(
        '--reservation-block',
        required=False,
        help='Name of the reservation block the host is associated with.',
    )
    parser.add_argument(
        '--current',
        action='store_true',
        help='Include current SBOM selection in the result.',
    )
    parser.add_argument(
        '--target',
        action='store_true',
        help='Include target SBOM selection in the result.',
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args: argparse.Namespace):
    """Run the get-version command."""
    if args.reservation_block and not args.reservation:
      raise exceptions.RequiredArgumentException(
          '--reservation',
          'Must be specified when --reservation-block is provided.',
      )

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    # Construct association
    association = []
    if args.reservation:
      association.append(f'reservations/{args.reservation}')
    if args.reservation_block:
      association.append(f'reservationBlocks/{args.reservation_block}')
    association_str = '/'.join(association) if association else ''
    args.association = association_str

    # Construct SBOM selections
    sbom_enum = (
        messages.HostsGetVersionRequest.SbomSelectionsValueListEntryValuesEnum
    )
    sbom_selections = []
    if args.current:
      sbom_selections.append(sbom_enum.SBOM_SELECTION_CURRENT)
    if args.target:
      sbom_selections.append(sbom_enum.SBOM_SELECTION_TARGET)

    host_ref = self.HOST_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetDefaultScopeLister(client),
        additional_params={'association': association_str or '""'},
    )

    return get_version_helper.RunGetVersion(
        holder, args, host_ref, sbom_selections, association_str
    )
