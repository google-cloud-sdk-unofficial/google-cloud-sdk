# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Command for detaching a disk from an instance."""

import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


class DetachDisk(base_classes.ReadWriteCommand):
  """Detach disks from Compute Engine virtual machine instances.

  *{command}* is used to detach disks from virtual machines.

  Detaching a disk without first unmounting it may result in
  incomplete I/O operations and data corruption.
  To unmount a persistent disk on a Linux-based image,
  ssh into the instance and run:

      $ sudo umount /dev/disk/by-id/google-DEVICE_NAME
  """

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCE_ARG.AddArgument(parser)
    disk_group = parser.add_mutually_exclusive_group(required=True)

    disk_name = disk_group.add_argument(
        '--disk',
        help='Specify a disk to remove by persistent disk name.')
    disk_name.detailed_help = """\
        Specifies a disk to detach by its resource name. If you specify a
        disk to remove by persistent disk name, then you must not specify its
        device name using the ``--device-name'' flag.
        """

    device_name = disk_group.add_argument(
        '--device-name',
        help=('Specify a disk to remove by the name the guest operating '
              'system sees.'))
    device_name.detailed_help = """\
        Specifies a disk to detach by its device name, which is the name
        that the guest operating system sees. The device name is set
        at the time that the disk is attached to the instance, and needs not be
        the same as the persistent disk name. If the disk's device name is
        specified, then its persistent disk name must not be specified
        using the ``--disk'' flag.
        """

  @property
  def service(self):
    return self.compute.instances

  @property
  def resource_type(self):
    return 'instances'

  def CreateReference(self, args):
    return instance_flags.INSTANCE_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))

  def GetGetRequest(self, args):
    return (self.service,
            'Get',
            self.messages.ComputeInstancesGetRequest(
                instance=self.ref.Name(),
                project=self.project,
                zone=self.ref.zone))

  def GetSetRequest(self, args, replacement, existing):
    removed_disk = list(
        set(disk.deviceName for disk in existing.disks) -
        set(disk.deviceName for disk in replacement.disks))[0]

    return (self.service,
            'DetachDisk',
            self.messages.ComputeInstancesDetachDiskRequest(
                deviceName=removed_disk,
                instance=self.ref.Name(),
                project=self.project,
                zone=self.ref.zone))

  def Modify(self, args, existing):
    replacement = copy.deepcopy(existing)

    if args.disk:
      disk_ref = self.resources.Parse(
          args.disk, collection='compute.disks',
          params={'zone': self.ref.zone})
      replacement.disks = [disk for disk in existing.disks
                           if disk.source != disk_ref.SelfLink()]

      if len(existing.disks) == len(replacement.disks):
        raise exceptions.ToolException(
            'Disk [{0}] is not attached to instance [{1}] in zone [{2}].'
            .format(disk_ref.Name(), self.ref.Name(), self.ref.zone))

    else:
      replacement.disks = [disk for disk in existing.disks
                           if disk.deviceName != args.device_name]

      if len(existing.disks) == len(replacement.disks):
        raise exceptions.ToolException(
            'No disk with device name [{0}] is attached to instance [{1}] in '
            'zone [{2}].'
            .format(args.device_name, self.ref.Name(), self.ref.zone))

    return replacement
