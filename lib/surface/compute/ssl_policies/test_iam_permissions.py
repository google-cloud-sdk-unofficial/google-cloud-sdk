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
"""Command for testing IAM permissions for SSL policies."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_policies import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.UniverseCompatible
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine SSL policy."""

  SSL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SSL_POLICY_ARG = flags.GetSslPolicyMultiScopeArgument()
    cls.SSL_POLICY_ARG.AddArgument(
        parser, operation_type='test-iam-permissions'
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

    ssl_policy_ref = self.SSL_POLICY_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
        default_scope=compute_scope.ScopeEnum.GLOBAL,
    )

    if ssl_policy_ref.Collection() == 'compute.regionSslPolicies':
      service = client.apitools_client.regionSslPolicies
      request = (
          client.messages.ComputeRegionSslPoliciesTestIamPermissionsRequest(
              project=ssl_policy_ref.project,
              region=ssl_policy_ref.region,
              resource=ssl_policy_ref.Name(),
              testPermissionsRequest=client.messages.TestPermissionsRequest(
                  permissions=args.permissions
              ),
          )
      )
    else:
      service = client.apitools_client.sslPolicies
      request = client.messages.ComputeSslPoliciesTestIamPermissionsRequest(
          project=ssl_policy_ref.project,
          resource=ssl_policy_ref.Name(),
          testPermissionsRequest=client.messages.TestPermissionsRequest(
              permissions=args.permissions
          ),
      )

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]


TestIamPermissions.detailed_help = {
    'brief': 'Test IAM permissions for a Compute Engine SSL policy.',
    'DESCRIPTION': (
        """\
        *{command}* tests the IAM permissions that a caller has on a Compute
        Engine SSL policy.
        """
    ),
    'EXAMPLES': (
        """\
        To test if the caller has the `compute.sslPolicies.list`
        permission on the regional SSL policy `my-ssl-policy` in
        region `us-central1`, run:

          $ {command} my-ssl-policy --region=us-central1 --permissions=compute.sslPolicies.list

        To test if the caller has the `compute.sslPolicies.list`
        permission on the global SSL policy `my-ssl-policy`, run:

          $ {command} my-ssl-policy --global --permissions=compute.sslPolicies.list
        """
    ),
}
