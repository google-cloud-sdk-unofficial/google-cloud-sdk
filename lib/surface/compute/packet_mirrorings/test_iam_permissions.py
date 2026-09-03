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
"""Command for testing IAM permissions for packet mirrorings."""

from typing import Any

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.packet_mirrorings import flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA,
    base.ReleaseTrack.PREVIEW,
)
@base.UniverseCompatible
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine packet mirroring policy."""

  detailed_help = {
      'brief': (
          'Test IAM permissions for a Compute Engine packet mirroring policy.'
      ),
      'DESCRIPTION': (
          """\
          *{command}* tests the IAM permissions that a caller has on a
          Compute Engine packet mirroring policy.

          Note: This operation is designed to be used for building
          permission-aware UIs and command-line tools, not for authorization
          checking. This operation may "fail open" without warning.
          """
      ),
      'EXAMPLES': (
          """\
          To test if the caller has `compute.packetMirrorings.get` permission on a packet mirroring policy `my-pm` in region `us-central1`, run:

            $ {command} my-pm --region=us-central1 --permissions=compute.packetMirrorings.get
          """
      ),
  }

  PACKET_MIRRORING_ARG = None

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor) -> None:
    cls.PACKET_MIRRORING_ARG = flags.PacketMirroringArgument()
    cls.PACKET_MIRRORING_ARG.AddArgument(
        parser, operation_type='test IAM permissions for'
    )
    parser.add_argument(
        '--permissions',
        metavar='PERMISSION',
        type=arg_parsers.ArgList(),
        required=True,
        help='The set of permissions to check for the resource.',
    )

  def Run(self, args: parser_extensions.Namespace) -> Any:
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    ref = self.PACKET_MIRRORING_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    request = client.messages.ComputePacketMirroringsTestIamPermissionsRequest(
        project=ref.project,
        region=ref.region,
        resource=ref.Name(),
        testPermissionsRequest=client.messages.TestPermissionsRequest(
            permissions=args.permissions
        ),
    )

    return client.MakeRequests([(
        client.apitools_client.packetMirrorings,
        'TestIamPermissions',
        request,
    )])[0]
