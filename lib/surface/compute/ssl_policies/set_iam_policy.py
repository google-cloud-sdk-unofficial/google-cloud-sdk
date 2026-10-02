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
"""Command to set IAM policy for an SSL policy."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_policies import flags
from googlecloudsdk.command_lib.compute.ssl_policies import ssl_policies_utils
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class SetIamPolicy(base.Command):
  """Set the IAM policy for a Compute Engine SSL policy."""

  SSL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SSL_POLICY_ARG = flags.GetSslPolicyMultiScopeArgument()
    cls.SSL_POLICY_ARG.AddArgument(parser, operation_type='setIamPolicy')
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    ssl_policy_ref = self.SSL_POLICY_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
    )

    policy = iam_util.ParsePolicyFile(args.policy_file, client.messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    return ssl_policies_utils.SetIamPolicy(ssl_policy_ref, client, policy)


SetIamPolicy.detailed_help = {
    'brief': 'Set the IAM policy for a Compute Engine SSL policy.',
    'DESCRIPTION': (
        """\
    Sets the IAM policy for the given SSL policy as defined in a
    JSON or YAML file.  """
    ),
    'EXAMPLES': (
        """\
    The following command will read an IAM policy defined in a JSON file
    'policy.json' and set it for the regional SSL policy `my-ssl-policy`:

      $ {command} my-ssl-policy policy.json --region=REGION

    The following commands will read an IAM policy defined in a JSON file
    'policy.json' and set it for the global SSL policy `my-ssl-policy`:

      $ {command} my-ssl-policy policy.json --global

      $ {command} my-ssl-policy policy.json

    See https://cloud.google.com/iam/docs/managing-policies for details of the
    policy file format and contents.
    """
    ),
    'API REFERENCE': (
        """\
    This command uses the compute API. The full documentation for this
    API can be found at: https://cloud.google.com/compute/"""
    ),
}
