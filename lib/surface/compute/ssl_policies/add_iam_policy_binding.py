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
"""Command to add IAM policy binding for an SSL policy."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_policies import flags
from googlecloudsdk.command_lib.compute.ssl_policies import ssl_policies_utils
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class AddIamPolicyBinding(base.Command):
  """Add an IAM policy binding to a Compute Engine SSL policy."""

  SSL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SSL_POLICY_ARG = flags.GetSslPolicyMultiScopeArgument()
    cls.SSL_POLICY_ARG.AddArgument(parser)
    iam_util.AddArgsForAddIamPolicyBinding(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    ssl_policy_ref = self.SSL_POLICY_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
    )

    policy = ssl_policies_utils.GetIamPolicy(ssl_policy_ref, client)
    iam_util.AddBindingToIamPolicy(
        client.messages.Binding, policy, args.member, args.role
    )

    return ssl_policies_utils.SetIamPolicy(ssl_policy_ref, client, policy)


AddIamPolicyBinding.detailed_help = {
    'brief': 'Add an IAM policy binding to a Compute Engine SSL policy.',
    'DESCRIPTION': (
        """\
  Add an IAM policy binding to a Compute Engine SSL policy.  """
    ),
    'EXAMPLES': (
        """\
  To add an IAM policy binding for the role of
  'compute.loadBalancerServiceUser' for the user 'test-user@gmail.com' with
  SSL policy 'my-ssl-policy' and region 'REGION', run:

      $ {command} my-ssl-policy --region=REGION \
        --member='user:test-user@gmail.com' \
        --role='roles/compute.loadBalancerServiceUser'

  To add an IAM policy binding for the role of
  'compute.loadBalancerServiceUser' for the user 'test-user@gmail.com' with
  global SSL policy 'my-ssl-policy', run either of the following:

      $ {command} my-ssl-policy --global \
        --member='user:test-user@gmail.com' \
        --role='roles/compute.loadBalancerServiceUser'

      $ {command} my-ssl-policy \
        --member='user:test-user@gmail.com' \
        --role='roles/compute.loadBalancerServiceUser'

  See https://cloud.google.com/iam/docs/managing-policies for details of
  policy role and member types.
  """
    ),
    'API REFERENCE': (
        """\
   This command uses the compute API. The full documentation for this
    API can be found at: https://cloud.google.com/compute/"""
    ),
}
