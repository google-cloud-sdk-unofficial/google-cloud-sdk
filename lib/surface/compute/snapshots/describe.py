# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for describing snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.snapshots import flags


def _GAArgs(parser):
  """Set Args based on Release Track."""
  Describe.SnapshotArg = flags.MakeSnapshotArg()
  Describe.SnapshotArg.AddArgument(parser, operation_type='describe')


def _BetaArgs(parser):
  Describe.SnapshotArg = flags.MakeSnapshotArgForRegionalSnapshots()
  Describe.SnapshotArg.AddArgument(parser, operation_type='describe')


def _AlphaArgs(parser):
  Describe.SnapshotArg = flags.MakeSnapshotArgForRegionalSnapshots()
  Describe.SnapshotArg.AddArgument(parser, operation_type='describe')


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.UniverseCompatible
class Describe(base.DescribeCommand):
  """Describe a Compute Engine snapshot."""

  @staticmethod
  def Args(parser):
    _GAArgs(parser)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args, support_region=False):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    snapshot_ref = Describe.SnapshotArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
        default_scope=compute_scope.ScopeEnum.GLOBAL,
    )

    if (
        support_region
        and snapshot_ref.Collection() == 'compute.regionSnapshots'
    ):

      request = messages.ComputeRegionSnapshotsGetRequest(
          **snapshot_ref.AsDict(),
      )

      return client.MakeRequests(
          [(client.apitools_client.regionSnapshots, 'Get', request)]
      )[0]

    request = messages.ComputeSnapshotsGetRequest(**snapshot_ref.AsDict())
    return client.MakeRequests(
        [(client.apitools_client.snapshots, 'Get', request)]
    )[0]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):

  @staticmethod
  def Args(parser):
    _BetaArgs(parser)

  def Run(self, args):
    return self._Run(
        args,
        support_region=True,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(Describe):

  @staticmethod
  def Args(parser):
    _AlphaArgs(parser)

  def Run(self, args):
    return self._Run(
        args,
        support_region=True,
    )


Describe.detailed_help = {
    'brief': 'Describe a Compute Engine snapshot',
    'DESCRIPTION': """
    *{command}* displays all data associated with a Compute Engine snapshot
    in a project.

    Given an existing snapshot is queried, successful output of this command
    looks like the following:

    ```
    creationTimestamp: '2018-05-07T10:45:46.988-07:00'
    diskSizeGb: '500'
    id: '1234567891234567890'
    kind: compute#snapshot
    labelFingerprint: 12345abcdWW=
    name: zs9utdhb8r1x
    selfLink: https://www.googleapis.com/compute/v1/projects/test-project-name/global/snapshots/snapshot-number
    sourceDisk: https://www.googleapis.com/compute/v1/projects/test-project-name/zones/us-central1-c/disks/test
    sourceDiskId: '1234567891234567890'
    status: READY
    storageBytes: '0'
    storageBytesStatus: UP_TO_DATE
    ```
    """,

    'EXAMPLES': """

    To run `{command}`, you'll need the name of a snapshot. To list existing
    snapshots by name, run:

      $ {parent_command} list

    To display specific details of an existing Compute Engine snapshot (like
    its creation time, status, and storage details), run:

      $ {command} SNAPSHOT_NAME --format="table(creationTimestamp, status, storageBytesStatus)"
        """,
}
