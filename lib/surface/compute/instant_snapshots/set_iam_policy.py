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
"""Command to set IAM policy for an instant snapshot."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instant_snapshots_utils as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instant_snapshots import flags as ips_flags
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(
    base.ReleaseTrack.GA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.PREVIEW,
)
@base.DefaultUniverseOnly
class SetIamPolicy(base.Command):
  """Set the IAM policy binding for a Compute Engine instant snapshot."""

  @classmethod
  def Args(cls, parser):
    cls.IPS_ARG = ips_flags.MakeInstantSnapshotArg()
    cls.IPS_ARG.AddArgument(parser, operation_type='set the IAM policy on')
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    ips_ref = self.IPS_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    policy = iam_util.ParsePolicyFile(args.policy_file, messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    ips_info = api_util.GetInstantSnapshotInfo(
        ips_ref, client.apitools_client, messages
    )
    request = ips_info.GetSetIamPolicyRequestMessage(policy)
    service = ips_info.GetService()

    result = client.MakeRequests([(service, 'SetIamPolicy', request)])[0]
    iam_util.LogSetIamPolicy(ips_ref.Name(), 'instant snapshot')
    return result


SetIamPolicy.detailed_help = {
    'brief': (
        'Set the IAM policy binding for a Compute Engine instant snapshot.'
    ),
    'DESCRIPTION': """\
        *{command}* sets the IAM policy for a Compute Engine instant
        snapshot as defined in a JSON or YAML file.
        """,
    'EXAMPLES': """\
        To set the IAM policy for the zonal instant snapshot
        'my-instant-snapshot' in zone 'ZONE' from a file 'policy.json',
        run:

            $ {command} my-instant-snapshot policy.json --zone=ZONE

        To set the IAM policy for the regional instant snapshot
        'my-instant-snapshot' in region 'REGION' from a file 'policy.json',
        run:

            $ {command} my-instant-snapshot policy.json --region=REGION

        See https://cloud.google.com/iam/docs/managing-policies for details
        of the policy file format and contents.
        """,
}
