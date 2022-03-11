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
"""Command for stopping async replication on disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags

DETAILED_HELP = {
    'brief':
        'Stop async replication on a Compute Engine persistent disk',
    'DESCRIPTION':
        """\
        *{command}* stops async replication on a Compute Engine persistent
        disk. This command can be invoked either on the primary or on the
        secondary disk. If stop replication is invoked on the primary disk,
        `--secondary-disk` and one of `--secondary-disk-zone` or
        `secondary-disk-region` must be provided.
        """,
    'EXAMPLES':
        """\
        When stopping async replication, be sure to include the `--zone` or `--region`
        option. To stop replication between primary disk 'my-disk-1' in zone
        us-east1-a and secondary disk 'my-disk-2' in us-west1-a:

          $ {command} my-disk-1 --zone=us-east1-a --secondary-disk=my-disk-2 --secondary-disk-zone=us-west1-a

        Alternatively, you can stop replication from the secondary disk:

          $ {command} my-disk-2 --zone=us-west1-a
        """,
}


def _CommonArgs(parser):
  """Add arguments used for parsing in all command tracks."""
  StopAsyncReplication.disks_arg.AddArgument(
      parser, operation_type='stop async replication')
  StopAsyncReplication.secondary_disk_arg.AddArgument(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class StopAsyncReplication(base.Command):
  """Stop Async Replication on Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    StopAsyncReplication.disks_arg = disks_flags.MakeDiskArg(plural=False)
    StopAsyncReplication.secondary_disk_arg = disks_flags.MakeSecondaryDiskArg()
    _CommonArgs(parser)

  def GetAsyncSecondaryDiskUri(self, args, compute_holder):
    secondary_disk_ref = None
    if args.secondary_disk:
      secondary_disk_ref = self.secondary_disk_arg.ResolveAsResource(
          args, compute_holder.resources)
      if secondary_disk_ref:
        return secondary_disk_ref.SelfLink()
    return None

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args):
    compute_holder = self._GetApiHolder()
    client = compute_holder.client

    disk_ref = StopAsyncReplication.disks_arg.ResolveAsResource(
        args,
        compute_holder.resources,
        scope_lister=flags.GetDefaultScopeLister(client))

    request = None
    secondary_disk_uri = self.GetAsyncSecondaryDiskUri(args, compute_holder)
    if disk_ref.Collection() == 'compute.disks':
      request = client.messages.ComputeDisksStopAsyncReplicationRequest(
          disk=disk_ref.Name(),
          project=disk_ref.project,
          zone=disk_ref.zone,
          disksStopAsyncReplicationRequest=client.messages
          .DisksStopAsyncReplicationRequest(
              asyncSecondaryDisk=secondary_disk_uri))
      request = (client.apitools_client.disks, 'StopAsyncReplication', request)
    elif disk_ref.Collection() == 'compute.regionDisks':
      request = client.messages.ComputeRegionDisksStopAsyncReplicationRequest(
          disk=disk_ref.Name(),
          project=disk_ref.project,
          region=disk_ref.region,
          regionDisksStopAsyncReplicationRequest=client.messages
          .RegionDisksStopAsyncReplicationRequest(
              asyncSecondaryDisk=secondary_disk_uri))
      request = (client.apitools_client.regionDisks, 'StopAsyncReplication',
                 request)
    return client.MakeRequests([request])


StopAsyncReplication.detailed_help = DETAILED_HELP
