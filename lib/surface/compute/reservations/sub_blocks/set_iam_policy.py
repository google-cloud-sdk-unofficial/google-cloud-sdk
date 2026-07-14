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
"""Command for setting IAM policy on a reservation sub-block."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.reservations import resource_args
from googlecloudsdk.command_lib.compute.reservations.sub_blocks import flags
from googlecloudsdk.command_lib.iam import iam_util

_DETAILED_HELP_TEXT = {
    'brief': (
        'Set the IAM policy binding for a Compute Engine reservation sub-block.'
    ),
    'DESCRIPTION': (
        """\
        Sets the IAM policy for the given reservation sub-block as defined in a
        JSON or YAML file.
        """
    ),
    'EXAMPLES': (
        """\
        To set the IAM policy on a reservation sub-block in reservation
        `my-reservation` in zone `us-central1-a` with block name `my-block`
        and sub-block name `my-sub-block` using a policy file `policy.json`, run:

          $ {command} my-reservation policy.json \\
              --zone=us-central1-a \\
              --block-name=my-block \\
              --sub-block-name=my-sub-block
        """
    ),
}


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.BETA, base.ReleaseTrack.GA, base.ReleaseTrack.PREVIEW
)
class SetIamPolicy(base.Command):
  """Set the IAM policy binding for a reservation sub-block."""

  detailed_help = _DETAILED_HELP_TEXT

  @staticmethod
  def Args(parser):
    resource_args.GetReservationResourceArg().AddArgument(
        parser, operation_type='set-iam-policy'
    )
    flags.AddDescribeFlags(parser)
    iam_util.AddArgForPolicyFile(parser)

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
        f'reservations/{reservation_ref.reservation}/'
        f'reservationBlocks/{args.block_name}'
    )

    policy = iam_util.ParsePolicyFile(args.policy_file, messages.Policy)
    request = (
        client.apitools_client.reservationSubBlocks,
        'SetIamPolicy',
        messages.ComputeReservationSubBlocksSetIamPolicyRequest(
            zone=reservation_ref.zone,
            project=reservation_ref.project,
            parentResource=parent_name,
            resource=args.sub_block_name,
            zoneSetNestedPolicyRequest=messages.ZoneSetNestedPolicyRequest(
                policy=policy,
            ),
        ),
    )

    response = client.MakeRequests(requests=[request], errors_to_collect=errors)
    if errors:
      utils.RaiseToolException(
          errors, error_message='Could not set IAM policy.'
      )

    return response[0]
