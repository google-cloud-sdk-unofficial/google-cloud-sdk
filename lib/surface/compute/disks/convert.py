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

import enum

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import disks_util
from googlecloudsdk.api_lib.compute import name_generator
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker


class _ConvertState(enum.Enum):
  SNAPSHOT_CREATED = 1
  DISK_RESTORED = 2
  ORIGINAL_DISK_DELETED = 3
  ORIGINAL_DISK_RECREATED = 4
  RESTORED_DISK_DELETED = 5
  SNAPSHOT_DELETED = 6


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

  def Run(self, args):
    self.holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    self.client = self.holder.client.apitools_client
    self.messages = self.holder.client.messages
    self.created_resources = {}
    self.state = None
    self.user_messages = ''

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

    if args.target_disk_type == 'hyperdisk-ml':
      raise exceptions.InvalidArgumentException(
          '--target-disk-type',
          'Hyperdisk ML is not supported for this command.',
      )

    # make sure disk is not attached to any instances
    disk_info = disks_util.GetDiskInfo(disk_ref, self.client, self.messages)
    original_disk = disk_info.GetDiskResource()
    if original_disk.users:
      raise exceptions.ToolException(
          'Disk is attached to instances. Please Detach the disk before'
          ' converting.'
      )
    try:
      with self._CreateProgressTracker(disk_ref.Name()):
        result = self._ConvertDisk(
            disk_ref, args.target_disk_type, original_disk.sizeGb
        )
    except Exception as e:
      raise e
    finally:
      self._CleanUp()
      if self.user_messages:
        log.error(self.user_messages)

    return result

  def _ConvertDisk(self, disk_ref, target_disk_type, size_gb):
    # create a snapshot of the disk
    snapshot_name = self._GenerateName(disk_ref)
    result = self._InsertSnapshot(disk_ref, snapshot_name)
    snapshot_ref = self.holder.resources.Parse(
        snapshot_name,
        params={'project': disk_ref.project},
        collection='compute.snapshots',
    )
    self._UpdateState(_ConvertState.SNAPSHOT_CREATED, snapshot_ref)
    # create a new disk from the snapshot with target disk type
    restored_disk_name = self._GenerateName(disk_ref)
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
            target_disk_type,
            size_gb,
        )
        or result
    )
    self._UpdateState(_ConvertState.DISK_RESTORED, restored_disk_ref)
    # delete the original disk
    result = self._DeleteDisk(disk_ref) or result
    self._UpdateState(_ConvertState.ORIGINAL_DISK_DELETED)

    # recreate the original disk with the new disk as source
    result = self._CloneDisk(disk_ref.Name(), restored_disk_ref) or result
    self._UpdateState(_ConvertState.ORIGINAL_DISK_RECREATED)

    # delete the restored disk because the original disk is recreated
    result = self._DeleteDisk(restored_disk_ref) or result
    self._UpdateState(_ConvertState.RESTORED_DISK_DELETED)

    # delete the snapshot because the disk is recreated
    result = self._DeleteSnapshot(snapshot_ref) or result
    self._UpdateState(_ConvertState.SNAPSHOT_DELETED)

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
    operation = self._MakeRequest(self.client.snapshots, 'Insert', request)
    operation_ref = self.holder.resources.Parse(
        operation.selfLink,
        collection='compute.globalOperations',
    )
    return waiter.WaitFor(
        poller.Poller(self.client.snapshots),
        operation_ref,
        custom_tracker=self._CreateNoOpProgressTracker(),
        max_wait_ms=None,
    )

  def _DeleteSnapshot(self, snapshot_ref):
    request = self.messages.ComputeSnapshotsDeleteRequest(
        snapshot=snapshot_ref.Name(),
        project=snapshot_ref.project,
    )
    operation = self._MakeRequest(self.client.snapshots, 'Delete', request)
    operation_ref = self.holder.resources.Parse(
        operation.selfLink,
        collection='compute.globalOperations',
    )
    return waiter.WaitFor(
        poller.DeletePoller(self.client.snapshots),
        operation_ref,
        custom_tracker=self._CreateNoOpProgressTracker(),
        max_wait_ms=None,
    )

  def _RestoreDiskFromSnapshot(
      self,
      restored_disk_ref,
      snapshot_ref,
      disk_type,
      size_gb,
  ):
    disk = self.messages.Disk(
        name=restored_disk_ref.Name(),
        type=disks_util.GetDiskTypeUri(
            disk_type, restored_disk_ref, self.holder
        ),
        sizeGb=size_gb,
        sourceSnapshot=snapshot_ref.SelfLink(),
    )

    request = self.messages.ComputeDisksInsertRequest(
        disk=disk,
        project=restored_disk_ref.project,
        zone=restored_disk_ref.zone,
    )
    operation = self._MakeRequest(self.client.disks, 'Insert', request)
    operation_ref = self.holder.resources.Parse(
        operation.selfLink,
        collection='compute.zoneOperations',
    )
    return waiter.WaitFor(
        poller.Poller(self.client.disks),
        operation_ref,
        custom_tracker=self._CreateNoOpProgressTracker(),
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
    operation = self._MakeRequest(self.client.disks, 'Delete', request)
    operation_ref = self.holder.resources.Parse(
        operation.selfLink,
        collection='compute.zoneOperations',
    )
    return waiter.WaitFor(
        poller.DeletePoller(self.client.disks),
        operation_ref,
        custom_tracker=self._CreateNoOpProgressTracker(),
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
    operation = self._MakeRequest(self.client.disks, 'Insert', request)
    operation_ref = self.holder.resources.Parse(
        operation.selfLink,
        collection='compute.zoneOperations',
    )
    operation_poller = poller.Poller(self.client.disks)
    return waiter.WaitFor(
        operation_poller,
        operation_ref,
        custom_tracker=self._CreateNoOpProgressTracker(),
        max_wait_ms=None,
    )

  def _MakeRequest(self, resource_client, method, request):
    errors_to_collect = []
    responses = self.holder.client.AsyncRequests(
        [(resource_client, method, request)], errors_to_collect
    )
    if errors_to_collect:
      raise core_exceptions.MultiError(errors_to_collect)
    if not responses:
      raise core_exceptions.InternalError('No response received')
    return responses[0]

  def _UpdateState(self, state, created_resource=None):
    self.state = state
    if created_resource:
      self.created_resources[state] = created_resource

  def _CleanUp(self):
    if self.state == _ConvertState.SNAPSHOT_CREATED:
      # restore disk failed
      self.user_messages = (
          'Please address erros below and rerun the command to retry.'
      )
      self._DeleteSnapshot(
          self.created_resources[_ConvertState.SNAPSHOT_CREATED]
      )
    elif self.state == _ConvertState.DISK_RESTORED:
      # delete original disk request failed
      self.user_messages = (
          'Please address erros below and rerun the command to retry.'
      )
      self._DeleteDisk(self.created_resources[_ConvertState.DISK_RESTORED])
      self._DeleteSnapshot(
          self.created_resources[_ConvertState.SNAPSHOT_CREATED]
      )
    elif self.state == _ConvertState.ORIGINAL_DISK_DELETED:
      # recreate original disk failed
      self.user_messages = """Please address errors below and use disk {0} as the source disk to recreate the original disk.
      You can also use the snapshot {1} to restore the original disk.
      """.format(
          self.created_resources[_ConvertState.DISK_RESTORED].Name(),
          self.created_resources[_ConvertState.SNAPSHOT_CREATED].Name(),
      )
    elif self.state == _ConvertState.ORIGINAL_DISK_RECREATED:
      # delete restored disk failed
      self.user_messages = """Conversion completed successfully.
          Encountered errors when cleaning up.
          Please delete the restored disk {0} and snapshot {1} manually.
      """.format(
          self.created_resources[_ConvertState.DISK_RESTORED].Name(),
          self.created_resources[_ConvertState.SNAPSHOT_CREATED].Name(),
      )
    elif self.state == _ConvertState.RESTORED_DISK_DELETED:
      self.user_messages = """Conversion completed successfully.
          Encountered errors when cleaning up.
          Please delete snapshot {1} manually.
      """.format(
          self.created_resources[_ConvertState.SNAPSHOT_CREATED].Name(),
      )

  def _CreateProgressTracker(self, disk_name):
    return progress_tracker.ProgressTracker(
        message=f'Converting disk {disk_name}...',
        aborted_message='Conversion aborted.',
    )

  def _CreateNoOpProgressTracker(self):
    return progress_tracker.NoOpProgressTracker(
        interruptable=True,
        aborted_message=''
    )
