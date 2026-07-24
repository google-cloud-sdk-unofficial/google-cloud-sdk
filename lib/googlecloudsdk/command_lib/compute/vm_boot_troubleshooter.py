# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Troubleshoot VM boot and kernel issue for ssh connection."""


from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import ssh_troubleshooter
from googlecloudsdk.command_lib.compute import ssh_troubleshooter_utils
from googlecloudsdk.core import log

_API_COMPUTE_CLIENT_NAME = 'compute'
_API_CLIENT_VERSION_V1 = 'v1'

VM_BOOT_PATTERNS = [
    'Security Violation',

    # GRUB not being able to find image.
    'Failed to load image',

    # OS emergency mode (emergency.target in systemd).
    'You are now being dropped into an emergency shell',
    'You are in (rescue|emergency) mode',
    r'Started \x1b?\[?.*Emergency Shell',
    r'Reached target \x1b?\[?.*Emergency Mode',

    # GRUB emergency shell.
    'Minimal BASH-like line editing is supported',
]

VM_BOOT_MESSAGE = (
    'The VM may not be running. The serial console logs show the VM has been '
    'unable to complete the boot process. Check your serial console logs to '
    'see if the VM has been dropped into an "emergency shell" or has reached '
    '"Emergency Mode". If that is the case, try restarting the VM to see if '
    'the problem is reproducible.\n')

KERNEL_PANIC_PATTERNS = [
    'Kernel panic - not syncing: Attempted to kill init!',
    'Kernel panic - not syncing: Fatal exception',
    'Kernel panic - not syncing: No working init found.',
    'Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block',
]

KERNEL_PANIC_MESSAGE = (
    'The VM is experiencing a kernel panic. This problem is specific to your '
    'VM and its workload, so you may need to investigate based on a "kernel '
    'panic" error in your serial console logs.\n')


# /etc/fstab: a device/filesystem entry could not be mounted -> emergency mode.
FSTAB_PATTERNS = [
    r'UUID=[\w-]+ does not exist',
    r'Timed out waiting for device.*/dev/',
    r'special device .* does not exist',
    r'Dependency failed for .*\.mount',
]
FSTAB_MESSAGE = (
    'The VM dropped into emergency mode because a device or filesystem listed '
    'in /etc/fstab could not be mounted. Identify the failing device (often a '
    'wrong or stale UUID) in the serial console logs, then comment out or fix '
    'the entry in /etc/fstab from a rescue environment. For instructions on '
    'setting up a rescue environment, see: '
    'https://cloud.google.com/compute/docs/troubleshooting/rescue-vm\n')

GRUB_PATTERNS = [
    r'error:.*(?:grub\.cfg|vmlinuz|initrd|initramfs).* not found',
    r'error:.*no such (?:partition|device)',
    r'error:.*unknown filesystem',
    r'error:.*(?:invalid magic number|invalid arch-independent ELF magic)',
    r'error:.*you need to load the kernel first',
    r'grub rescue>',
]
GRUB_MESSAGE = (
    'The GRUB bootloader could not find or load its configuration or the '
    'kernel image (for example a missing /boot/grub/grub.cfg or vmlinuz) and '
    'stopped at the GRUB shell. Reinstall GRUB and regenerate its config from '
    'a rescue environment (grub-install + update-grub, or grub2-mkconfig on '
    'RHEL-family images). For instructions on setting up a rescue environment, '
    'see: https://cloud.google.com/compute/docs/troubleshooting/rescue-vm\n')

INITRAMFS_PATTERNS = [
    r'dracut-initqueue\[\d+\]:.*timeout',
    r'Failed to mount /sysroot',
    r'Dependency failed for /sysroot',
    r'ALERT!.*does not exist.*Dropping to a shell',
    r'Gave up waiting for root (?:file system|device)',
    r'dracut: FATAL:',
]
INITRAMFS_MESSAGE = (
    'The initramfs could not mount the root filesystem (for example a dracut '
    'timeout waiting for the root device, a /sysroot mount failure, or a drop '
    'to the initramfs shell). Verify the root= kernel parameter and root '
    'device UUID, and rebuild the initramfs from a rescue environment '
    '(update-initramfs -u on Debian-family, dracut -f on RHEL-family). For '
    'instructions on setting up a rescue environment, see: '
    'https://cloud.google.com/compute/docs/troubleshooting/rescue-vm\n')

FILESYSTEM_PATTERNS = [
    r'Bad magic number in super-block',
    r'EXT4-fs error \(device',
    r'XFS \([\w-]+\): ' +
    r'(?:Metadata corruption detected|Metadata CRC error detected|Corruption)',
    r'BTRFS (?:error|critical) \(device',
    r'open_ctree failed',
]
FILESYSTEM_MESSAGE = (
    'A filesystem on the VM is corrupt (for example a bad superblock or '
    'ext4/XFS/Btrfs corruption). Run a filesystem check on the unmounted disk '
    'from a rescue environment (fsck for ext, xfs_repair for XFS). If the disk '
    'is unrecoverable, restore it from a snapshot. For instructions on '
    'setting up a rescue environment, see: '
    'https://cloud.google.com/compute/docs/troubleshooting/rescue-vm\n')

SELINUX_PATTERNS = [
    r'Failed to load SELinux policy',
    r'Unable to load SELinux policy',
]
SELINUX_MESSAGE = (
    'The VM failed to boot because SELinux could not load its policy and init '
    'froze. From a rescue environment, trigger a relabel (touch /.autorelabel) '
    'or temporarily disable SELinux (add selinux=0 to the kernel command '
    'line), then investigate /etc/selinux. For instructions on '
    'setting up a rescue environment, see: '
    'https://cloud.google.com/compute/docs/troubleshooting/rescue-vm\n')

SWITCHROOT_PATTERNS = [
    r'Failed to switch root',
    r'Target filesystem doesn.t have requested /sbin/init',
    r'No working init found',
    r'run-init: [^\n]*: No such file or directory',
]
SWITCHROOT_MESSAGE = (
    'The VM mounted its root filesystem but could not hand off to init '
    '(missing or broken /sbin/init, or a failed switch_root). From a rescue '
    'environment, verify /sbin/init exists and its shared libraries are '
    'intact, and reinstall systemd if it is broken. For instructions on '
    'setting up a rescue environment, see: '
    'https://cloud.google.com/compute/docs/troubleshooting/rescue-vm\n')

_BOOT_CAUSE_CHECKS = [
    (FSTAB_PATTERNS, 'fstab_issue', FSTAB_MESSAGE),
    (GRUB_PATTERNS, 'grub_issue', GRUB_MESSAGE),
    (INITRAMFS_PATTERNS, 'initramfs_issue', INITRAMFS_MESSAGE),
    (FILESYSTEM_PATTERNS, 'filesystem_issue', FILESYSTEM_MESSAGE),
    (SELINUX_PATTERNS, 'selinux_issue', SELINUX_MESSAGE),
    (SWITCHROOT_PATTERNS, 'switchroot_issue', SWITCHROOT_MESSAGE),
]


class VMBootTroubleshooter(ssh_troubleshooter.SshTroubleshooter):
  """Check VM boot and kernel panic issues.

  Attributes:
    project: The project object.
    zone: str, the zone name.
    instance: The instance object.
  """

  def __init__(self, project, zone, instance):
    self.project = project
    self.zone = zone
    self.instance = instance
    self.compute_client = apis.GetClientInstance(_API_COMPUTE_CLIENT_NAME,
                                                 _API_CLIENT_VERSION_V1)
    self.compute_message = apis.GetMessagesModule(_API_COMPUTE_CLIENT_NAME,
                                                  _API_CLIENT_VERSION_V1)
    self.issues = {}

  def check_prerequisite(self):
    return

  def cleanup_resources(self):
    return

  def troubleshoot(self):
    log.status.Print('---- Checking VM boot status ----')
    sc_log = ssh_troubleshooter_utils.GetSerialConsoleLog(
        self.compute_client, self.compute_message, self.instance.name,
        self.project.name, self.zone)

    # Cause-specific boot failures first, so we report the real root cause
    # and a targeted fix instead of a generic "check your logs" message.
    for patterns, key, message in _BOOT_CAUSE_CHECKS:
      if ssh_troubleshooter_utils.SearchPatternErrorInLog(patterns, sc_log):
        self.issues[key] = message

    # Kernel panic is a distinct symptom class.
    if ssh_troubleshooter_utils.SearchPatternErrorInLog(
        KERNEL_PANIC_PATTERNS, sc_log):
      self.issues['kernel_panic'] = KERNEL_PANIC_MESSAGE

    # Generic fallback: a boot stall we could not attribute to a specific cause.
    if not self.issues and ssh_troubleshooter_utils.SearchPatternErrorInLog(
        VM_BOOT_PATTERNS, sc_log):
      self.issues['boot_issue'] = VM_BOOT_MESSAGE

    log.status.Print('VM boot: {0} issue(s) found.\n'.format(len(self.issues)))
    for message in self.issues.values():
      log.status.Print(message)
