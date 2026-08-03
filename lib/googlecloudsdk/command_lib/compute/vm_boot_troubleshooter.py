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

import re

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import ssh_troubleshooter
from googlecloudsdk.command_lib.compute import ssh_troubleshooter_utils
from googlecloudsdk.core import log

_API_COMPUTE_CLIENT_NAME = 'compute'
_API_CLIENT_VERSION_V1 = 'v1'


# Markers that begin a new boot session on the GCE serial console, ordered
# by boot stage (earliest first). SeaBIOS prints its banner on every BIOS
# boot; BdsDxe / 'UEFI: Attempting' print on every UEFI boot; GRUB and the
# kernel banner cover buffers where firmware output has scrolled out.
_BOOT_SESSION_MARKERS = [
    r'SeaBIOS \(version',
    r'BdsDxe: loading Boot',
    r'UEFI: Attempting to start image',
    r'Welcome to GRUB!',
    r'Linux version \d',
]


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
    'Kernel panic - not syncing: hung_task: blocked tasks',
    r'Kernel panic - not syncing: [Oo]ut of memory',
    r'panic_on_oom is (?:selected|enabled)',
    'Kernel panic - not syncing: Fatal Machine check',
    'Kernel panic - not syncing: NMI: Not continuing',
    # Corrupt vmlinuz. The EFI decompression stub halts with
    # '-- System halted'; the line-start '-- ' prefix is unique to the
    # stub (normal shutdown prints 'System halted.' without dashes).
    r'(?:XZ|LZ4|ZSTD|gzip)[- ]compressed data is corrupt',
    r'^\s*-- System halted',
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

# Root filesystem remounted read-only after disk errors. This is the
# kernel's runtime response to a failing disk (errors=remount-ro),
# distinct from on-disk corruption found at mount time
# (FILESYSTEM_PATTERNS).
READONLY_FS_PATTERNS = [
    r'EXT4-fs \([\w-]+\): Remounting filesystem read-only',
    r'Remounting filesystem read-only',
    # Device-bound with a lookahead excluding loop/sr/fd/ram/zram
    # devices: loop I/O errors are routine snapd noise on Ubuntu GCE
    # images, sr0/fd0 are phantom CD-ROM/floppy probes; none of these
    # can be a GCE boot disk.
    r'blk_update_request: I/O error, dev (?!loop|sr\d|fd\d|ram\d|zram)[\w-]+',
    r'I/O error, dev (?!loop|sr\d|fd\d|ram\d|zram)[\w-]+, sector \d+',
    r'Buffer I/O error on dev (?!loop|sr\d|fd\d|ram\d|zram)[\w-]+',
]
READONLY_FS_MESSAGE = (
    'A filesystem on the VM was remounted read-only after disk I/O '
    'errors, so writes (including SSH logins that need to write) can '
    'fail. Check the serial console logs for the device reporting '
    'errors, snapshot the disk, then run a filesystem check on the '
    'unmounted disk from a rescue environment (fsck for ext, xfs_repair '
    'for XFS). For instructions on setting up a rescue environment, '
    'see: https://cloud.google.com/compute/docs/troubleshooting/rescue-vm\n')

# Boot disk out of space: the guest agent cannot write SSH keys or
# temporary files, so key-based SSH provisioning fails.
DISK_FULL_PATTERNS = [
    # Exclude ENOSPC sources that do not mean a full disk: inotify
    # watch exhaustion and cgroup limits on container hosts.
    (r'^(?!.*(?:inotify|directory watch|/sys/fs/cgroup)).*' +
     r'No space left on device[ \t]*$'),
    r'No usable temporary directory found',
]
DISK_FULL_MESSAGE = (
    'The boot disk is out of space, which can prevent the guest agent '
    'from writing SSH keys and block logins. Resize the boot disk '
    '(gcloud compute disks resize DISK_NAME --zone=ZONE '
    '--size=NEW_SIZE_GB, then restart the VM so the filesystem '
    'expands), or free space from a rescue environment. For '
    'instructions on setting up a rescue environment, see: '
    'https://cloud.google.com/compute/docs/troubleshooting/rescue-vm\n')

# The kernel out-of-memory killer ran. If it killed sshd or the guest
# agent, SSH fails while the VM reports RUNNING.
OOM_PATTERNS = [
    # Bound to the PID / gfp_mask= tail so quoted prose cannot match.
    r'Out of memory: Kill(?:ed)? process \d+',
    r'invoked oom-killer: gfp_mask=',
    r'oom-kill:constraint=',
]
OOM_MESSAGE = (
    'The VM ran out of memory and the kernel terminated one or more '
    'processes; if sshd or the guest agent was killed, SSH fails even '
    'though the VM is running. Identify the killed process in the '
    'serial console logs, then resize the VM to a larger machine type '
    '(gcloud compute instances set-machine-type VM_NAME --zone=ZONE '
    '--machine-type=NEW_TYPE, VM must be stopped) or reduce the '
    'workload\'s memory usage.\n')

# cloud-init provisioning failed: SSH keys, users, or network config
# may not have been applied (Ubuntu images rely on cloud-init for
# these).
CLOUD_INIT_PATTERNS = [
    # Bound to the cloud-init[PID]: journald prefix so a generic Python
    # traceback from another service can never match.
    r'cloud-init\[\d+\]:.*(?:Traceback|failed to run|Can not apply stage)',
    # Bound to cloud-init unit vocabulary; cannot fire on benign unit
    # failures (apt-daily, fwupd, ...).
    r'Failed to start .*cloud[- ]?init',
    r'Failed to start .*cloud-(?:config|final)',
]
CLOUD_INIT_MESSAGE = (
    'cloud-init failed during boot, so SSH keys, users, or network '
    'configuration may not have been provisioned. Check '
    '/var/log/cloud-init.log (over the serial console, or from a '
    'rescue environment if the VM is unreachable), validate the '
    'instance user-data, and re-run with "sudo cloud-init clean '
    '--logs" followed by a reboot. For instructions on setting up a '
    'rescue environment, see: '
    'https://cloud.google.com/compute/docs/troubleshooting/rescue-vm\n')

_BOOT_CAUSE_CHECKS = [
    (FSTAB_PATTERNS, 'fstab_issue', FSTAB_MESSAGE),
    (GRUB_PATTERNS, 'grub_issue', GRUB_MESSAGE),
    (INITRAMFS_PATTERNS, 'initramfs_issue', INITRAMFS_MESSAGE),
    (FILESYSTEM_PATTERNS, 'filesystem_issue', FILESYSTEM_MESSAGE),
    (SELINUX_PATTERNS, 'selinux_issue', SELINUX_MESSAGE),
    (SWITCHROOT_PATTERNS, 'switchroot_issue', SWITCHROOT_MESSAGE),
    (READONLY_FS_PATTERNS, 'readonly_fs_issue', READONLY_FS_MESSAGE),
    (DISK_FULL_PATTERNS, 'disk_full_issue', DISK_FULL_MESSAGE),
    (CLOUD_INIT_PATTERNS, 'cloud_init_issue', CLOUD_INIT_MESSAGE),
    (OOM_PATTERNS, 'oom_issue', OOM_MESSAGE),
]


def _FilterSessionLogToLastBoot(sc_log):
  """Filters the serial log down to the last boot session.

  The serial console buffer persists across in-place reboots, so errors
  from a previous, already-resolved boot failure would otherwise still
  match. Markers are tried in boot-stage order and the first marker type
  present wins (at its LAST occurrence): if the firmware banner is in the
  buffer, its last occurrence is always the start of the most recent
  session, and windowing there keeps the whole session including
  GRUB-stage errors that happen before the kernel banner.

  If no marker is found (boot output rotated out of the ~1 MB buffer, or
  the buffer was wiped by a VM stop), the full log is returned: no marker
  means no newer boot session exists in the buffer, so scanning everything
  cannot resurface a stale session.

  Args:
    sc_log: str, the full serial console (port 1) contents.

  Returns:
    str, the log content belonging to the most recent boot session, or
    the full log when no boot session marker is present.
  """
  for marker in _BOOT_SESSION_MARKERS:
    if matches := list(re.finditer(marker, sc_log)):
      return sc_log[matches[-1].start():]
  return sc_log


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

    # Scope matching to the current boot: the buffer survives in-place
    # reboots, and failures from an already-fixed boot must not be
    # reported as the current root cause.
    sc_log = _FilterSessionLogToLastBoot(sc_log)

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
