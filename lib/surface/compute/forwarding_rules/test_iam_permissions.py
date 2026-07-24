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
"""Command for testing IAM permissions for forwarding rules."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine forwarding rule."""

  FORWARDING_RULE_ARG = None

  @staticmethod
  def Args(parser):
    TestIamPermissions.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    TestIamPermissions.FORWARDING_RULE_ARG.AddArgument(
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

    forwarding_rule_ref = (
        TestIamPermissions.FORWARDING_RULE_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(client),
        )
    )

    if forwarding_rule_ref.Collection() == 'compute.forwardingRules':
      service = client.apitools_client.forwardingRules
      request = client.messages.ComputeForwardingRulesTestIamPermissionsRequest(
          project=forwarding_rule_ref.project,
          region=forwarding_rule_ref.region,
          resource=forwarding_rule_ref.Name(),
          testPermissionsRequest=client.messages.TestPermissionsRequest(
              permissions=args.permissions
          ),
      )
    else:
      service = client.apitools_client.globalForwardingRules
      request = (
          client.messages.ComputeGlobalForwardingRulesTestIamPermissionsRequest(
              project=forwarding_rule_ref.project,
              resource=forwarding_rule_ref.Name(),
              testPermissionsRequest=client.messages.TestPermissionsRequest(
                  permissions=args.permissions
              ),
          )
      )

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]


TestIamPermissions.detailed_help = {
    'brief': 'Test IAM permissions for a Compute Engine forwarding rule.',
    'DESCRIPTION': """\
        *{command}* tests the IAM permissions that a caller has on a Compute
        Engine forwarding rule.
        """,
    'EXAMPLES': """\
        To test if the caller has the `compute.forwardingRules.setIamPolicy`
        permission on the regional forwarding rule `my-forwarding-rule` in
        region `us-central1`, run:

          $ {command} my-forwarding-rule --region=us-central1 --permissions=compute.forwardingRules.setIamPolicy

        To test if the caller has the `compute.globalForwardingRules.setIamPolicy`
        permission on the global forwarding rule `my-forwarding-rule`, run:

          $ {command} my-forwarding-rule --global --permissions=compute.globalForwardingRules.setIamPolicy
        """,
}
