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
"""Test IAM permissions for an instant snapshot group command."""

from typing import Any
import frozendict
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute.instant_snapshot_groups import (
    flags as isg_flags,
)

_DETAILED_HELP = frozendict.frozendict({
    'brief': (
        'Test IAM permissions for a Compute Engine instant snapshot group.'
    ),
    'DESCRIPTION': (
        """\
        *{command}* tests the IAM permissions that a caller has on a Compute
        Engine instant snapshot group.
        """
    ),
    'EXAMPLES': (
        """\
        To test if the caller has the
        'compute.instantSnapshotGroups.get' permission on the
        instant snapshot group 'instant-snapshot-group-1' in zone
        'us-east1-a', run:

            $ {command} instant-snapshot-group-1 \\
                --zone=us-east1-a \\
                --permissions=compute.instantSnapshotGroups.get
        """
    ),
})


def _CommonArgs(parser: parser_arguments.ArgumentInterceptor) -> None:
  """A helper function to build args based on different API version."""
  TestIamPermissions.ISG_ARG = isg_flags.MakeInstantSnapshotGroupArg()
  TestIamPermissions.ISG_ARG.AddArgument(
      parser, operation_type='test IAM permissions'
  )
  parser.add_argument(
      '--permissions',
      metavar='PERMISSION',
      type=arg_parsers.ArgList(),
      required=True,
      help='Set of permissions to check for the resource.',
  )


@base.ReleaseTracks(
    base.ReleaseTrack.GA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.ALPHA,
)
@base.DefaultUniverseOnly
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine instant snapshot group."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor) -> None:
    _CommonArgs(parser)

  def _Run(self, args: parser_extensions.Namespace) -> Any:
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    isg_ref = TestIamPermissions.ISG_ARG.ResolveAsResource(
        args, holder.resources
    )

    if isg_ref.Collection() == 'compute.instantSnapshotGroups':
      service = client.apitools_client.instantSnapshotGroups
      request_type = (
          messages.ComputeInstantSnapshotGroupsTestIamPermissionsRequest
      )
      request = request_type(
          project=isg_ref.project,
          zone=isg_ref.zone,
          resource=isg_ref.Name(),
          testPermissionsRequest=messages.TestPermissionsRequest(
              permissions=args.permissions
          ),
      )
    else:
      service = client.apitools_client.regionInstantSnapshotGroups
      request_type = (
          messages.ComputeRegionInstantSnapshotGroupsTestIamPermissionsRequest
      )
      request = request_type(
          project=isg_ref.project,
          region=isg_ref.region,
          resource=isg_ref.Name(),
          testPermissionsRequest=messages.TestPermissionsRequest(
              permissions=args.permissions
          ),
      )

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]

  def Run(self, args: parser_extensions.Namespace) -> Any:
    return self._Run(args)
