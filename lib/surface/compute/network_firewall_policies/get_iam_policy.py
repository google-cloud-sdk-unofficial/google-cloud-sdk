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
"""Command to get IAM policy for a network firewall policy."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.network_firewall_policies import client
from googlecloudsdk.api_lib.compute.network_firewall_policies import region_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags


@base.UniverseCompatible
class GetIamPolicy(base.Command):
  """Get the IAM policy for a Compute Engine network firewall policy."""

  @staticmethod
  def Args(parser):
    flags.NetworkFirewallPolicyArgument(
        required=True, operation='get IAM policy'
    ).AddArgument(parser, operation_type='get')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = flags.NetworkFirewallPolicyArgument(
        required=True, operation='get IAM policy'
    ).ResolveAsResource(args, holder.resources)

    if hasattr(ref, 'region'):
      network_firewall_policy = region_client.RegionNetworkFirewallPolicy(
          ref,
          compute_client=holder.client,
      )
    else:
      network_firewall_policy = client.NetworkFirewallPolicy(
          ref,
          compute_client=holder.client,
      )

    return network_firewall_policy.GetIamPolicy()


GetIamPolicy.detailed_help = {
    'brief':
        'Get the IAM policy for a Compute Engine network firewall policy.',
    'DESCRIPTION':
        """\
        *{command}* displays the IAM policy associated with a Compute Engine
      network firewall policy in a project. If formatted as JSON, the output can
      be edited and used as a policy file for set-iam-policy. The output
      includes an "etag" field identifying the version emitted and allowing
      detection of concurrent policy updates; see $ {parent} set-iam-policy for
      additional details.
        """,
    'EXAMPLES':
        """\
        To print the IAM policy for the global network firewall policy `my-policy`, run:

          $ {command} my-policy --global

        To print the IAM policy for the regional network firewall policy `my-policy` (in region `REGION`), run:

          $ {command} my-policy --region=REGION
        """,
}
