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
"""Command for getting the version of a reservation sub-block."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.reservations import resource_args
from googlecloudsdk.command_lib.compute.reservations.sub_blocks import flags
from googlecloudsdk.core import exceptions as core_exceptions


class GetVersionPoller(poller.Poller):
  """Custom poller that returns the operation response directly.

  This avoids the AttributeError caused by the default Poller trying to
  re-fetch the resource using incompatible field names.
  """

  def __init__(self, resource_service, is_current):
    super(GetVersionPoller, self).__init__(resource_service)
    self.is_current = is_current

  def GetResult(self, operation):
    """Returns a nested dictionary for structured formatting."""
    metadata = getattr(operation, 'getVersionOperationMetadata', None)
    if not metadata:
      return None

    # Decode the metadata into a Python dictionary
    metadata_dict = encoding.MessageToPyValue(metadata)
    sbom_info = metadata_dict.get('inlineSbomInfo', {})

    # Return a nested dictionary using the component name maps directly
    if self.is_current:
      return {
          'currentComponentVersions': sbom_info.get(
              'currentComponentVersions', {}
          )
      }
    else:
      return {
          'targetComponentVersions': sbom_info.get(
              'targetComponentVersions', {}
          )
      }


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetVersion(base.Command):
  """Get the version of a reservation sub-block."""

  @staticmethod
  def Args(parser):
    resource_args.GetReservationResourceArg().AddArgument(
        parser, operation_type='get-version')
    flags.AddGetVersionFlags(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    reservation_ref = resource_args.GetReservationResourceArg(
    ).ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    parent_name = f'reservations/{reservation_ref.reservation}/reservationBlocks/{args.block_name}'

    sbom_selections_enum = (
        messages.ReservationSubBlocksGetVersionRequest.SbomSelectionsValueListEntryValuesEnum
    )
    sbom_selections = []
    if args.current:
      sbom_selections.append(sbom_selections_enum.SBOM_SELECTION_CURRENT)
    if args.target:
      sbom_selections.append(sbom_selections_enum.SBOM_SELECTION_TARGET)

    # Create the inner message instance for the request body
    body_message = messages.ReservationSubBlocksGetVersionRequest()
    if sbom_selections:
      body_message.sbomSelections = sbom_selections

    # Create the outer request instance with path/query parameters
    request = messages.ComputeReservationSubBlocksGetVersionRequest(
        parentName=parent_name,
        zone=reservation_ref.zone,
        project=reservation_ref.project,
        reservationSubBlock=args.sub_block_name,
        # Assign the inner message to the body field
        reservationSubBlocksGetVersionRequest=body_message
    )

    errors = []
    responses = client.AsyncRequests(
        [(client.apitools_client.reservationSubBlocks, 'GetVersion', request)],
        errors_to_collect=errors
    )

    # Check for and raise any RPC errors
    if errors:
      raise core_exceptions.MultiError(errors)

    # Parse the response
    operation_refs = [holder.resources.Parse(r.selfLink) for r in responses]
    operation_ref = operation_refs[0]

    operation_poller = GetVersionPoller(
        holder.client.apitools_client.reservationSubBlocks,
        is_current=args.current
    )
    result = waiter.WaitFor(
        operation_poller,
        operation_ref,
        'Waiting for operation [{}] to complete'.format(operation_ref.Name()),
    )
    return result


GetVersion.detailed_help = {
    'EXAMPLES': (
        """\
    To get the current version of a reservation sub-block in reservation
    exr-1 in ZONE with block name block-1 and sub-block name sub-block-1, run:

      $ {command} exr-1 --zone=ZONE --block-name=block-1 \
          --sub-block-name=sub-block-1 --current
    """
    ),
}
