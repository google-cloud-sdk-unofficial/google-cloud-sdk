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
"""Command to set IAM policy for a recoverable snapshot."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.recoverable_snapshots import flags
from googlecloudsdk.command_lib.iam import iam_util


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class SetIamPolicy(base.Command):
  """Set the IAM policy binding for a Compute Engine recoverable snapshot."""

  @classmethod
  def Args(cls, parser):
    cls.RECOVERABLE_SNAPSHOT_ARG = flags.MakeRecoverableSnapshotArg()
    cls.RECOVERABLE_SNAPSHOT_ARG.AddArgument(
        parser, operation_type='set the IAM policy on'
    )
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    recoverable_snapshot_ref = (
        self.RECOVERABLE_SNAPSHOT_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(client),
            default_scope=compute_scope.ScopeEnum.GLOBAL,
        )
    )

    policy = iam_util.ParsePolicyFile(args.policy_file, messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    # Build the SetIamPolicy request for the global recoverable snapshot
    request = messages.ComputeRecoverableSnapshotsSetIamPolicyRequest(
        project=recoverable_snapshot_ref.project,
        resource=recoverable_snapshot_ref.Name(),
        globalSetPolicyRequest=messages.GlobalSetPolicyRequest(policy=policy),
    )

    service = client.apitools_client.recoverableSnapshots
    result = client.MakeRequests([(service, 'SetIamPolicy', request)])[0]
    iam_util.LogSetIamPolicy(
        recoverable_snapshot_ref.Name(), 'recoverable snapshot'
    )
    return result


SetIamPolicy.detailed_help = {
    'brief': (
        'Set the IAM policy binding for a Compute Engine recoverable snapshot.'
    ),
    'DESCRIPTION': """\
        *{command}* sets the IAM policy for a Compute Engine recoverable
        snapshot as defined in a JSON or YAML file.
        """,
    'EXAMPLES': """\
        To set the IAM policy for the recoverable snapshot
        'my-recoverable-snapshot' from a file 'policy.json', run:

            $ {command} my-recoverable-snapshot policy.json

        See https://cloud.google.com/iam/docs/managing-policies for details
        of the policy file format and contents.
        """,
}
