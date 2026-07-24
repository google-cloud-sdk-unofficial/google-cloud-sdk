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
"""Command to test IAM permissions for a recoverable snapshot."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.recoverable_snapshots import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class TestIamPermissions(base.Command):
  """Test the IAM permissions for a Compute Engine recoverable snapshot."""

  @classmethod
  def Args(cls, parser):
    cls.RECOVERABLE_SNAPSHOT_ARG = flags.MakeRecoverableSnapshotArg()
    cls.RECOVERABLE_SNAPSHOT_ARG.AddArgument(
        parser, operation_type='test IAM permissions for'
    )
    parser.add_argument(
        '--permissions',
        metavar='PERMISSION',
        type=arg_parsers.ArgList(),
        required=True,
        help='The set of permissions to check for the resource.',
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    recoverable_snapshot_ref = (
        self.RECOVERABLE_SNAPSHOT_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(client),
            default_scope=compute_scope.ScopeEnum.GLOBAL,
        )
    )

    test_permissions_request = messages.TestPermissionsRequest(
        permissions=args.permissions
    )

    # Build the TestIamPermissions request for the global recoverable snapshot
    request = messages.ComputeRecoverableSnapshotsTestIamPermissionsRequest(
        project=recoverable_snapshot_ref.project,
        resource=recoverable_snapshot_ref.Name(),
        testPermissionsRequest=test_permissions_request,
    )

    service = client.apitools_client.recoverableSnapshots
    (result,) = client.MakeRequests([(service, 'TestIamPermissions', request)])
    return result


TestIamPermissions.detailed_help = {
    'brief': (
        'Test the IAM permissions for a Compute Engine recoverable snapshot.'
    ),
    'DESCRIPTION': """\
        *{command}* tests the IAM permissions that a caller has on a
        Compute Engine recoverable snapshot.
        """,
    'EXAMPLES': """\
        To test if the caller has `compute.recoverableSnapshots.list`
        permission on the recoverable snapshot 'my-recoverable-snapshot', run:

            $ {command} my-recoverable-snapshot \\
                --permissions=compute.recoverableSnapshots.list
        """,
}
