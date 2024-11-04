# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command for converting a disk to a different type."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import disks_util
from googlecloudsdk.api_lib.compute import name_generator
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Convert(base.RestoreCommand):
  """Convert a Compute Engine disk into a new disk type or new format."""

  _DISK_ARG = disks_flags.MakeDiskArg(plural=False)

  @staticmethod
  def Args(parser):
    Convert._DISK_ARG.AddArgument(parser)
    parser.add_argument(
        '--target-disk-type',
        completer=completers.DiskTypesCompleter,
        required=True,
        help="""Specifies the type of disk to convert to. To get a
        list of available disk types, run `gcloud compute disk-types list`.
        """,
    )
    disks_flags.AddProvisionedThroughputFlag(parser, arg_parsers)
    disks_flags.AddProvisionedIopsFlag(parser, arg_parsers)
    disks_flags.AddKeepOldDiskArgs(parser)

  def Run(self, args):
    self.holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    self.client = self.holder.client.apitools_client
    self.messages = self.holder.client.messages

    disk_ref = self._DISK_ARG.ResolveAsResource(
        args,
        self.holder.resources,
        scope_lister=flags.GetDefaultScopeLister(self.holder.client),
    )

    if disk_ref.Collection() == 'compute.regionDisks':
      raise exceptions.InvalidArgumentException(
          '--region',
          'Regional disks are not supported for this command.'
      )

    # make sure disk is not attached to any instances
    disk_info = disks_util.GetDiskInfo(disk_ref, self.client, self.messages)
    original_disk = disk_info.GetDiskResource()
    if original_disk.users:
      raise exceptions.ToolException(
          'Disk is attached to instances. Please Detach the disk before'
          ' converting.'
      )
    # create a snapshot of the disk
    snapshot_name = self._GenerateName(disk_ref)
    result = self._InsertSnapshot(disk_ref, snapshot_name)
    snapshot_ref = self.holder.resources.Parse(
        snapshot_name,
        params={'project': disk_ref.project},
        collection='compute.snapshots',
    )
    # create a new disk from the snapshot with target disk type
    restored_disk_name = args.target_disk_name or self._GenerateName(disk_ref)
    restored_disk_ref = self.holder.resources.Parse(
        restored_disk_name,
        params={'project': disk_ref.project,
                'zone': disk_ref.zone},
        collection='compute.disks',
    )
    result = (
        self._RestoreDiskFromSnapshot(
            restored_disk_ref,
            snapshot_ref,
            args.target_disk_type,
            original_disk.sizeGb,
            provisioned_throughput=args.provisioned_throughput,
            provisioned_iops=args.provisioned_iops,
        )
        or result
    )
    # delete the original disk
    result = self._DeleteDisk(disk_ref) or result

    # recreate the original disk with the new disk as source
    result = self._CloneDisk(disk_ref.Name(), restored_disk_ref) or result

    # delete the restored disk because the original disk is recreated
    result = self._DeleteDisk(restored_disk_ref) or result

    # delete the snapshot because the disk is recreated
    result = self._DeleteSnapshot(snapshot_ref) or result

    return result

  def _InsertSnapshot(self, disk_ref, snapshot_name):
    request = self.messages.ComputeSnapshotsInsertRequest(
        project=disk_ref.project,
        snapshot=self.messages.Snapshot(
            name=snapshot_name,
            sourceDisk=disk_ref.SelfLink(),
            snapshotType=self.messages.Snapshot.SnapshotTypeValueValuesEnum.STANDARD,
        ),
    )
    operation = self.client.snapshots.Insert(request)
    operation_ref = self.holder.resources.Parse(
        operation.selfLink,
        collection='compute.globalOperations',
    )
    return waiter.WaitFor(
        poller.Poller(self.client.snapshots),
        operation_ref,
        'Creating snapshot {0}...'.format(snapshot_name),
        max_wait_ms=None,
    )

  def _DeleteSnapshot(self, snapshot_ref):
    request = self.messages.ComputeSnapshotsDeleteRequest(
        snapshot=snapshot_ref.Name(),
        project=snapshot_ref.project,
    )
    operation = self.client.snapshots.Delete(request)
    operation_ref = self.holder.resources.Parse(
        operation.selfLink,
        collection='compute.globalOperations',
    )
    return waiter.WaitFor(
        poller.DeletePoller(self.client.snapshots),
        operation_ref,
        'Deleting snapshot {0}...'.format(snapshot_ref.Name()),
        max_wait_ms=None,
    )

  def _RestoreDiskFromSnapshot(
      self,
      restored_disk_ref,
      snapshot_ref,
      disk_type,
      size_gb,
      provisioned_throughput=None,
      provisioned_iops=None,
  ):
    disk = self.messages.Disk(
        name=restored_disk_ref.Name(),
        type=disks_util.GetDiskTypeUri(
            disk_type, restored_disk_ref, self.holder
        ),
        sizeGb=size_gb,
        sourceSnapshot=snapshot_ref.SelfLink(),
    )
    if provisioned_throughput:
      disk.provisionedThroughput = provisioned_throughput
    if provisioned_iops:
      disk.provisionedIops = provisioned_iops

    request = self.messages.ComputeDisksInsertRequest(
        disk=disk,
        project=restored_disk_ref.project,
        zone=restored_disk_ref.zone,
    )
    operation = self.client.disks.Insert(request)
    operation_ref = self.holder.resources.Parse(
        operation.selfLink,
        collection='compute.zoneOperations',
    )
    return waiter.WaitFor(
        poller.Poller(self.client.disks),
        operation_ref,
        'Restoring disk {0}...'.format(restored_disk_ref.Name()),
        max_wait_ms=None,
    )

  def _GenerateName(self, resource_ref):
    return '{0}-{1}'.format(
        name_generator.GenerateRandomName(), resource_ref.Name()
    )[:64]

  def _DeleteDisk(self, disk_ref):
    request = self.messages.ComputeDisksDeleteRequest(
        disk=disk_ref.Name(),
        project=disk_ref.project,
        zone=disk_ref.zone,
    )
    operation = self.client.disks.Delete(request)
    operation_ref = self.holder.resources.Parse(
        operation.selfLink,
        collection='compute.zoneOperations',
    )
    return waiter.WaitFor(
        poller.DeletePoller(self.client.disks),
        operation_ref,
        'Deleting disk {0}...'.format(disk_ref.Name()),
        max_wait_ms=None,
    )

  def _CloneDisk(self, original_disk_name, restored_disk_ref):
    disk = self.messages.Disk(
        name=original_disk_name,
        sourceDisk=restored_disk_ref.SelfLink(),
    )
    request = self.messages.ComputeDisksInsertRequest(
        disk=disk,
        project=restored_disk_ref.project,
        zone=restored_disk_ref.zone,
    )
    operation = self.client.disks.Insert(request)
    operation_ref = self.holder.resources.Parse(
        operation.selfLink,
        collection='compute.zoneOperations',
    )
    operation_poller = poller.Poller(self.client.disks)
    return waiter.WaitFor(
        operation_poller,
        operation_ref,
        'Recreating disk {0}...'.format(original_disk_name),
        max_wait_ms=None,
    )
