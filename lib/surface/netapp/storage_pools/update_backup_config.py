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
"""Updates backup config of a volume in a specified Storage Pool."""

from googlecloudsdk.api_lib.netapp.storage_pools import client as storagepools_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.storage_pools import flags as storagepools_flags
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBackupConfig(base.Command):
  """A command to update backup config of a volume in an ONTAP-mode Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': (
          """\
          Updates the backup configuration of a volume within the specified Storage Pool.
          """
      ),
      'EXAMPLES': (
          """\
          The following command updates the backup configuration of a volume with UUID 5dc61a44-3d99-11f1-b8ff-39021cc41d7a in an ONTAP-mode Storage Pool named NAME.

              $ {command} NAME --location=us-central1 --volume-uuid=5dc61a44-3d99-11f1-b8ff-39021cc41d7a --backup-config=backup-vault=my-vault,enable-scheduled-backups=true
          """
      ),
  }

  @staticmethod
  def Args(parser):
    storagepools_flags.AddStoragePoolUpdateBackupConfigArgs(parser)

  def Run(self, args):
    """Run the update-backup-config command."""
    storagepool_ref = args.CONCEPTS.storage_pool.Parse()
    client = storagepools_client.StoragePoolsClient(
        release_track=self._RELEASE_TRACK
    )

    backup_config = args.backup_config
    updated_fields = []
    if backup_config.get('backup-policies') is not None:
      updated_fields.append('backup_config.backup_policies')
    if backup_config.get('backup-vault') is not None:
      updated_fields.append('backup_config.backup_vault')
    if backup_config.get('enable-scheduled-backups') is not None:
      updated_fields.append('backup_config.scheduled_backup_enabled')
    update_mask = ','.join(updated_fields)

    result = client.UpdateBackupConfig(
        storagepool_ref,
        args.volume_uuid,
        args.backup_config,
        update_mask,
        args.async_,
    )
    if args.async_:
      prefix = self.ReleaseTrack().prefix
      command_prefix = prefix + ' ' if prefix else ''
      log.status.Print(
          'Check the status of the update backup config operation by polling '
          f'the operation ID received:\n  $ gcloud {command_prefix}netapp '
          f'operations describe {result.name}'
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateBackupConfigAlpha(UpdateBackupConfig):
  """Update backup config of a volume in an ONTAP-mode Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA
