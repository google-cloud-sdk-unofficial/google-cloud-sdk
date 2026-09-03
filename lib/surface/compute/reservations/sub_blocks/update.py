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
"""Command for updating a reservation sub-block."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.reservations import resource_args
from googlecloudsdk.command_lib.compute.reservations.sub_blocks import flags
from googlecloudsdk.core import log


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a sub-block within a Compute Engine reservation."""

  @staticmethod
  def Args(parser):
    resource_args.GetReservationResourceArg(
        help_text=(
            'The name of the reservation containing the sub-block to update.'
        )
    ).AddArgument(parser, operation_type='update')
    flags.AddDescribeFlags(parser)
    parser.add_argument(
        '--retention-priority',
        type=int,
        help='The new retention priority for the reservation sub-block.',
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    reservation_ref = (
        resource_args.GetReservationResourceArg().ResolveAsResource(
            args,
            holder.resources,
            default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=compute_flags.GetDefaultScopeLister(client),
        )
    )

    parent_name = (
        f'reservations/{reservation_ref.reservation}/'
        f'reservationBlocks/{args.block_name}'
    )

    sub_block_resource = client.messages.ReservationSubBlock()
    update_mask_paths = []

    if args.IsSpecified('retention_priority'):
      sub_block_resource.retentionPriority = args.retention_priority
      update_mask_paths.append('retentionPriority')

    request = client.messages.ComputeReservationSubBlocksUpdateRequest(
        parentName=parent_name,
        zone=reservation_ref.zone,
        project=reservation_ref.project,
        reservationSubBlock=args.sub_block_name,
        reservationSubBlockResource=sub_block_resource,
        updateMask=','.join(update_mask_paths),
    )

    responses = client.MakeRequests(
        [(client.apitools_client.reservationSubBlocks, 'Update', request)],
        log_result=False,
    )

    if args.IsSpecified('retention_priority'):
      log.UpdatedResource(
          args.sub_block_name,
          kind='reservation sub-block retention priority to {}'.format(
              args.retention_priority
          ),
      )
    else:
      log.UpdatedResource(
          args.sub_block_name,
          kind='reservation sub-block',
      )

    return responses


Update.detailed_help = {
    'EXAMPLES': (
        """\
    To update reservation exr-1 in ZONE with block name block-1 and
    sub block name sub-block-1 to have retention priority 100, run:

      $ {command} exr-1 --zone=ZONE --block-name=block-1 \
          --sub-block-name=sub-block-1 \
          --retention-priority=100
    """
    ),
}
