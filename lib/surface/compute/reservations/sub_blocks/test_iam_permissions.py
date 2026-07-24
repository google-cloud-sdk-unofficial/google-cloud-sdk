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
"""Command for testing IAM permissions on a reservation sub-block."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.reservations import resource_args
from googlecloudsdk.command_lib.compute.reservations.sub_blocks import flags

_DETAILED_HELP_TEXT = {
    "brief": "Test IAM permissions on a Compute Engine reservation sub-block.",
    "DESCRIPTION": (
        """\
        Returns the subset of permissions that the caller has on the specified
        Compute Engine reservation sub-block.
        """
    ),
    "EXAMPLES": (
        """\
        To test the 'compute.reservations.get' and
        'compute.reservations.update' permissions on a reservation sub-block
        named 'my-sub-block', which is part of block 'my-block' under
        reservation 'my-reservation' in zone 'us-central1-a', run:

          $ {command} my-reservation \\
              --zone=us-central1-a \\
              --block-name=my-block \\
              --sub-block-name=my-sub-block \\
              --permissions=compute.reservations.get,compute.reservations.update
        """
    ),
}


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.BETA, base.ReleaseTrack.GA, base.ReleaseTrack.PREVIEW
)
class TestIamPermissions(base.Command):
  """Test IAM permissions on a Compute Engine reservation sub-block."""

  detailed_help = _DETAILED_HELP_TEXT

  @staticmethod
  def Args(parser):
    resource_args.GetReservationResourceArg().AddArgument(
        parser, operation_type="test-iam-permissions"
    )
    flags.AddDescribeFlags(parser)
    parser.add_argument(
        "--permissions",
        required=True,
        type=arg_parsers.ArgList(),
        metavar="PERMISSION",
        help="Set of permissions to check for the resource.",
    )

  def Run(self, args):
    errors = []

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
    parent_name = (
        f"reservations/{reservation_ref.reservation}/"
        f"reservationBlocks/{args.block_name}"
    )

    request = (
        client.apitools_client.reservationSubBlocks,
        "TestIamPermissions",
        messages.ComputeReservationSubBlocksTestIamPermissionsRequest(
            zone=reservation_ref.zone,
            project=reservation_ref.project,
            parentResource=parent_name,
            resource=args.sub_block_name,
            testPermissionsRequest=messages.TestPermissionsRequest(
                permissions=args.permissions
            ),
        ),
    )

    response = client.MakeRequests(requests=[request], errors_to_collect=errors)
    if errors:
      utils.RaiseToolException(
          errors, error_message="Could not test IAM permissions for sub-block."
      )

    return response[0]
