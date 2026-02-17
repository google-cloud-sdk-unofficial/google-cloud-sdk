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
"""Command for getting the effective recycle bin rule for snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.snapshots import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class GetEffectiveRecycleBinRule(base.DescribeCommand):
  """Get the effective recycle bin rule for a Compute Engine snapshot."""

  @staticmethod
  def Args(parser):
    GetEffectiveRecycleBinRule.SnapshotArg = flags.MakeSnapshotArg()
    GetEffectiveRecycleBinRule.SnapshotArg.AddArgument(
        parser, operation_type='get the effective recycle bin rule for')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    snapshot_ref = GetEffectiveRecycleBinRule.SnapshotArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    request = client.messages.ComputeSnapshotsGetEffectiveRecycleBinRuleRequest(
        project=snapshot_ref.project, snapshot=snapshot_ref.snapshot
    )
    return client.MakeRequests([(
        client.apitools_client.snapshots,
        'GetEffectiveRecycleBinRule',
        request,
    )])[0]


GetEffectiveRecycleBinRule.detailed_help = {
    'brief': (
        'Returns the effective recycle bin rule for a Compute Engine snapshot'
    ),
    'DESCRIPTION': """
    *{command}* displays the effective recycle bin rule for a Compute Engine snapshot
    in a project.

    Given an existing snapshot is queried, successful output of this command
    looks like the following:

    ```
    retentionDurationDays: '7'
    ```
    """,

    'EXAMPLES': """

    To get the effective recycle bin rule for a snapshot, run:

      $ {command} SNAPSHOT_NAME
        """,
}
