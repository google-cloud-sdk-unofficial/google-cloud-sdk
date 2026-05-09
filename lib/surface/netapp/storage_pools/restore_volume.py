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
"""Restores a backup to a volume in a specified ONTAP-mode Storage Pool."""

import textwrap
from googlecloudsdk.api_lib.netapp.storage_pools import client as storagepools_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.storage_pools import flags as storagepools_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RestoreVolume(base.Command):
  """Restores a backup to a volume in a specified ONTAP-mode Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          Restores a backup to a volume within the specified Storage Pool.

          This command supports both full backup restore and selective file restore:

          *Full Backup Restore*: The `--volume-uuid` must reference a Data Protection (DP) volume where the backup will be restored.

          *File Restore*: The `--volume-uuid` must reference a Read-Write (RW) volume where the file(s) from the backup will be restored. For file restore, `--file-list` and `--restore-destination-path` must be included in the request payload.

          For the complete backup restore, users should first create a Data Protection volume via the ONTAP Mode APIs whereas a Read-Write volume must be created first for selective file restore.
          """),
      'EXAMPLES': textwrap.dedent("""\
          The following command restores full backup from a backup with full resource name `projects/my-project/locations/us-central1/backupVaults/my-vault/backups/backup-1` to an ONTAP-mode volume with UUID 5dc61a44-3d99-11f1-b8ff-39021cc41d7a in Storage Pool named NAME.

              $ {command} NAME --location=us-central1 --backup=projects/my-project/locations/us-central1/backupVaults/my-vault/backups/backup-1 --volume-uuid=5dc61a44-3d99-11f1-b8ff-39021cc41d7a

          The following command restores file1.txt from the same backup to an ONTAP-mode volume with UUID 5dc61a44-3d99-11f1-b8ff-39021cc41d7a in Storage Pool named NAME to the directory /my_restore_destination.

              $ {command} NAME --location=us-central1 --backup=projects/my-project/locations/us-central1/backupVaults/my-vault/backups/backup-1 --volume-uuid=5dc61a44-3d99-11f1-b8ff-39021cc41d7a --file-list=/path/to/file1.txt --restore-destination-path=/my_restore_destination
          """),
  }

  @classmethod
  def Args(cls, parser):
    storagepools_flags.AddStoragePoolRestoreVolumeArgs(parser)

  def Run(self, args):
    """Run the restore command."""
    storagepool_ref = args.CONCEPTS.storage_pool.Parse()
    backup_ref = args.CONCEPTS.backup.Parse()
    client = storagepools_client.StoragePoolsClient(
        release_track=self._RELEASE_TRACK
    )

    warning = (
        'You are about to restore from a backup to a volume in ONTAP-mode'
        f' Storage Pool {storagepool_ref.RelativeName()}.\nAre you sure?'
    )
    if not console_io.PromptContinue(message=warning):
      return None

    result = client.RestoreVolume(
        storagepool_ref,
        backup_ref.RelativeName(),
        args.file_list,
        args.volume_uuid,
        args.restore_destination_path,
        args.async_,
    )
    if args.async_:
      prefix = self.ReleaseTrack().prefix
      command_prefix = prefix + ' ' if prefix else ''
      log.status.Print(
          'Check the status of the restore volume operation by polling the'
          f' operation ID received:\n$ gcloud {command_prefix}netapp operations'
          f' describe {result.name}'
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RestoreVolumeAlpha(RestoreVolume):
  """Restore a backup to a volume in an ONTAP-mode Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA
