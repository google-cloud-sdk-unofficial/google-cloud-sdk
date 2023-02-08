# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Update snapshot schedule policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags
from googlecloudsdk.command_lib.compute.resource_policies import util


def _CommonArgs(parser):
  """A helper function to build args."""
  flags.MakeResourcePolicyArg().AddArgument(parser)
  flags.AddCommonArgs(parser)
  flags.AddCycleFrequencyArgs(
      parser,
      flag_suffix='schedule',
      start_time_help="""\
Start time for the disk snapshot schedule in UTC. For example, `--start-time="15:00"`.
""",
      cadence_help='Snapshot schedule',
      supports_weekly=True,
      supports_hourly=True,
      required=False)
  flags.AddSnapshotLabelArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class UpdateSnapshotSchedule(base.UpdateCommand):
  """Update a Compute Engine Snapshot Schedule Resource Policy."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages
    policy_ref = flags.MakeResourcePolicyArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    resource_policy = util.MakeDiskSnapshotSchedulePolicyForUpdate(
        policy_ref, args, messages)

    patch_request = messages.ComputeResourcePoliciesPatchRequest(
        resourcePolicy=policy_ref.Name(),
        resourcePolicyResource=resource_policy,
        project=policy_ref.project,
        region=policy_ref.region)
    service = holder.client.apitools_client.resourcePolicies
    return client.MakeRequests([(service, 'Patch', patch_request)])

UpdateSnapshotSchedule.detailed_help = {
    'DESCRIPTION':
        """\
Update a Compute Engine Snapshot Schedule Resource Policy.
""",
    'EXAMPLES':
        """\
The following command updates a Compute Engine Snapshot Schedule Resource Policy to take a daily snapshot taken at 13:00 UTC

  $ {command} my-resource-policy --region=REGION --start-time=13:00 --daily-schedule
"""
}
