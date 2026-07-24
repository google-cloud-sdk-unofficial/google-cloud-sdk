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
"""Command to set IAM policy for an organization firewall policy."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.firewall_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.firewall_policies import firewall_policies_utils
from googlecloudsdk.command_lib.compute.firewall_policies import flags
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
class SetIamPolicy(base.Command):
  """Set the IAM policy for a Compute Engine organization firewall policy."""

  FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_POLICY_ARG = flags.FirewallPolicyArgument(
        required=True, operation='set IAM policy')
    cls.FIREWALL_POLICY_ARG.AddArgument(parser, operation_type='get')
    parser.add_argument(
        '--organization',
        help=('Organization ID in which the organization firewall policy is '
              'to be set. Must be set if FIREWALL_POLICY is '
              'short name.'))
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources, with_project=False)

    org_firewall_policy = client.OrgFirewallPolicy(
        ref=ref,
        compute_client=holder.client,
        resources=holder.resources,
        version=str(self.ReleaseTrack()).lower(),
    )

    fp_id = firewall_policies_utils.GetFirewallPolicyId(
        org_firewall_policy, ref.Name(), organization=args.organization)

    policy, _ = iam_util.ParsePolicyFileWithUpdateMask(
        args.policy_file, holder.client.messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    result = org_firewall_policy.SetIamPolicy(policy, fp_id=fp_id)
    log.status.Print(f'Updated IAM policy for firewall_policy [{fp_id}].')
    return result


SetIamPolicy.detailed_help = {
    'brief':
        'Set the IAM policy for a Compute Engine organization firewall policy.',
    'DESCRIPTION':
        """\
        Sets the IAM policy for the given organization firewall policy as defined in a JSON or YAML file.
        """,
    'EXAMPLES':
        """\
        The following command will read an IAM policy defined in a JSON file
       'policy.json' and set it for the organization firewall policy `my-policy`:

         $ {command} my-policy policy.json --organization=123456789

       To set the IAM policy for the organization firewall policy with numeric ID `987654321`, run:

         $ {command} 987654321 policy.json

       See https://cloud.google.com/iam/docs/managing-policies for details of the
       policy file format and contents.
         """,
}
