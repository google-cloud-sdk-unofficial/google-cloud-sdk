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
"""Command to get IAM policy for an SSL policy."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_policies import flags
from googlecloudsdk.command_lib.compute.ssl_policies import ssl_policies_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for a Compute Engine SSL policy."""

  SSL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SSL_POLICY_ARG = flags.GetSslPolicyMultiScopeArgument()
    cls.SSL_POLICY_ARG.AddArgument(parser, operation_type='getIamPolicy')
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    ssl_policy_ref = self.SSL_POLICY_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
    )

    return ssl_policies_utils.GetIamPolicy(ssl_policy_ref, client)


GetIamPolicy.detailed_help = {
    'brief': 'Get the IAM policy for a Compute Engine SSL policy.',
    'DESCRIPTION': (
        """\
      *{command}* displays the IAM policy associated with a
    Compute Engine SSL policy in a project. If formatted as JSON,
    the output can be edited and used as a policy file for
    set-iam-policy. The output includes an "etag" field
    identifying the version emitted and allowing detection of
    concurrent policy updates; see $ {parent_command} set-iam-policy
    for additional details.  """
    ),
    'EXAMPLES': (
        """\
    To print the IAM policy for a given regional SSL policy, run:

      $ {command} my-ssl-policy --region=REGION

    To print the IAM policy for a given global SSL policy, run either of
    the following:

      $ {command} my-ssl-policy --global

      $ {command} my-ssl-policy
      """
    ),
    'API REFERENCE': (
        """\
        This command uses the compute API. The full documentation for this
    API can be found at: https://cloud.google.com/compute/"""
    ),
}
