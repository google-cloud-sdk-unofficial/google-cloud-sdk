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
"""Command for testing IAM permissions on instant snapshots."""

from typing import Any

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instant_snapshots import flags as ips_flags


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.PREVIEW,
)
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine instant snapshot."""

  detailed_help = {
      'brief': (
          'Test IAM permissions for a Compute Engine instant snapshot.'
      ),
      'DESCRIPTION': (
          """\
          *{command}* tests the IAM permissions that a caller has on a
          Compute Engine instant snapshot.

          Note: This operation is designed to be used for building
          permission-aware UIs and command-line tools, not for authorization
          checking. This operation may "fail open" without warning.
          """
      ),
      'EXAMPLES': (
          """\
          To test if the caller has `compute.instantSnapshots.getIamPolicy`
          permission on a zonal instant snapshot `my-snapshot` in zone `us-east1-a`, run:

            $ {command} my-snapshot --zone=us-east1-a \\
                --permissions=compute.instantSnapshots.getIamPolicy

          To test permissions on a regional instant snapshot `my-rsnapshot` in region `us-east1`, run:

            $ {command} my-rsnapshot --region=us-east1 \\
                --permissions=compute.instantSnapshots.getIamPolicy
          """
      ),
  }

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor) -> None:
    cls.ips_arg = ips_flags.MakeInstantSnapshotArg(plural=False)
    cls.ips_arg.AddArgument(parser, operation_type='test IAM permissions for')
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
    apitools_client = client.apitools_client
    messages = client.messages
    resources = holder.resources

    ips_ref = self.ips_arg.ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    test_permissions_request = messages.TestPermissionsRequest(
        permissions=args.permissions
    )

    if ips_ref.Collection() == 'compute.instantSnapshots':
      service = apitools_client.instantSnapshots
      request = messages.ComputeInstantSnapshotsTestIamPermissionsRequest(
          resource=ips_ref.Name(),
          zone=ips_ref.zone,
          project=ips_ref.project,
          testPermissionsRequest=test_permissions_request,
      )
    elif ips_ref.Collection() == 'compute.regionInstantSnapshots':
      service = apitools_client.regionInstantSnapshots
      request = messages.ComputeRegionInstantSnapshotsTestIamPermissionsRequest(
          resource=ips_ref.Name(),
          region=ips_ref.region,
          project=ips_ref.project,
          testPermissionsRequest=test_permissions_request,
      )
    else:
      raise ValueError(
          'Unknown reference type {0}'.format(ips_ref.Collection())
      )

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]
