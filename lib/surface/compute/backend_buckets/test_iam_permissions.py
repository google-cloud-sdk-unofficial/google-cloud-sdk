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
"""Command to test IAM permissions for a backend bucket."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.backend_buckets import backend_buckets_utils
from googlecloudsdk.command_lib.compute.backend_buckets import flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.PREVIEW)
@base.DefaultUniverseOnly
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine backend bucket."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_BUCKET_ARG_IAM.AddArgument(
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
    backend_bucket_ref = (
        flags.GLOBAL_REGIONAL_BACKEND_BUCKET_ARG_IAM.ResolveAsResource(
            args,
            holder.resources,
            default_scope=compute_scope.ScopeEnum.GLOBAL,
            scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
        )
    )

    return backend_buckets_utils.TestIamPermissions(
        backend_bucket_ref, client, args.permissions
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class TestIamPermissionsBeta(TestIamPermissions):
  pass


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class TestIamPermissionsAlpha(TestIamPermissionsBeta):
  pass


TestIamPermissions.detailed_help = {
    'brief': 'Test IAM permissions for a Compute Engine backend bucket.',
    'DESCRIPTION': (
        """\
        *{command}* tests the IAM permissions that a caller has on a
        Compute Engine backend bucket.

        Note: This operation is designed to be used for building
        permission-aware UIs and command-line tools, not for authorization
        checking. This operation may "fail open" without warning.
        """
    ),
    'EXAMPLES': (
        """\
        To test if the caller has `compute.backendBuckets.get` and
        `compute.backendBuckets.update` permissions on a global backend bucket
        `my-backend-bucket`, run:

          $ {command} my-backend-bucket \\
              --permissions=compute.backendBuckets.get,compute.backendBuckets.update

        To test permissions on a regional backend bucket `my-backend-bucket` in region `us-central1`, run:

          $ {command} my-backend-bucket --region=us-central1 \\
              --permissions=compute.regionBackendBuckets.get,compute.regionBackendBuckets.update
        """
    ),
    'API REFERENCE': (
        """\
        This command uses the compute API. The full documentation for this
        API can be found at: https://cloud.google.com/compute/"""
    ),
}
