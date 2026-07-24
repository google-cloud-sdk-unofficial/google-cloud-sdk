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
"""Command to set IAM policy for a network firewall policy."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.network_firewall_policies import client
from googlecloudsdk.api_lib.compute.network_firewall_policies import region_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log


@base.UniverseCompatible
class SetIamPolicy(base.Command):
  """Set the IAM policy binding for a Compute Engine network firewall policy."""

  @staticmethod
  def Args(parser):
    flags.NetworkFirewallPolicyArgument(
        required=True, operation='set IAM policy'
    ).AddArgument(parser, operation_type='get')
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = flags.NetworkFirewallPolicyArgument(
        required=True, operation='set IAM policy'
    ).ResolveAsResource(args, holder.resources)

    # Note: Compute network firewall policies API expects v3 policy.
    # We parse the file and override policy.version to max supported.
    messages = holder.client.messages
    policy, _ = iam_util.ParsePolicyFileWithUpdateMask(
        args.policy_file, messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

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

    result = network_firewall_policy.SetIamPolicy(policy)
    log.status.Print(f'Updated IAM policy for firewall_policy [{ref.Name()}].')
    return result


SetIamPolicy.detailed_help = {
    'brief':
        'Set the IAM policy binding for a Compute Engine network firewall '
        'policy.',
    'DESCRIPTION':
        """\
        Sets the IAM policy for the given network firewall policy as defined in a
      JSON or YAML file.
        """,
    'EXAMPLES':
        """\
        The following command will read an IAM policy defined in a JSON file
      'policy.json' and set it for the global network firewall policy `my-policy`:

        $ {command} my-policy policy.json --global

      The following command will read an IAM policy defined in a JSON file
      'policy.json' and set it for the regional network firewall policy `my-policy`
      (in region `REGION`):

        $ {command} my-policy policy.json --region=REGION

      See https://cloud.google.com/iam/docs/managing-policies for details of the
      policy file format and contents.
        """,
}
