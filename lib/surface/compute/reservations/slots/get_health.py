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
"""Command for getting the health of a reservation slot."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.reservations import resource_args
from googlecloudsdk.command_lib.compute.reservations.slots import flags
from googlecloudsdk.core import exceptions as core_exceptions


class GetHealthPoller(poller.Poller):
  """Custom poller that returns the getHealth operation metadata directly.

  This avoids the AttributeError caused by the default Poller trying to
  re-fetch the resource using incompatible field names.
  """

  def GetResult(self, operation):
    """Returns metadata dictionary for structured formatting."""
    metadata = getattr(operation, 'getHealthOperationMetadata', None)
    if not metadata:
      return None

    return encoding.MessageToPyValue(metadata)


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetHealth(base.Command):
  """Get the health of a reservation slot."""

  @staticmethod
  def Args(parser):
    resource_args.GetReservationResourceArg().AddArgument(
        parser, operation_type='get-health'
    )
    flags.AddGetHealthFlags(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    reservation_ref = (
        resource_args.GetReservationResourceArg().ResolveAsResource(
            args,
            holder.resources,
            default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=compute_flags.GetDefaultScopeLister(client),
        )
    )

    parent_name = f'reservations/{reservation_ref.reservation}/reservationBlocks/{args.block_name}/reservationSubBlocks/{args.sub_block_name}'

    request = messages.ComputeReservationSlotsGetHealthRequest(
        parentName=parent_name,
        zone=reservation_ref.zone,
        project=reservation_ref.project,
        reservationSlot=args.slot_name,
    )

    errors = []
    responses = client.AsyncRequests(
        [(client.apitools_client.reservationSlots, 'GetHealth', request)],
        errors_to_collect=errors,
    )

    if errors:
      raise core_exceptions.MultiError(errors)

    operation_refs = [holder.resources.Parse(r.selfLink) for r in responses]
    operation_ref = operation_refs[0]

    operation_poller = GetHealthPoller(client.apitools_client.reservationSlots)
    return waiter.WaitFor(
        operation_poller,
        operation_ref,
        'Waiting for operation [{}] to complete'.format(operation_ref.Name()),
    )


GetHealth.detailed_help = {
    'EXAMPLES': (
        """\
    To get the health of a reservation slot in reservation exr-1 in ZONE
    with block name block-1, sub-block name sub-block-1 and slot name slot-1, run:

      $ {command} exr-1 --zone=ZONE --block-name=block-1 \
          --sub-block-name=sub-block-1 --slot-name=slot-1
    """
    ),
}
