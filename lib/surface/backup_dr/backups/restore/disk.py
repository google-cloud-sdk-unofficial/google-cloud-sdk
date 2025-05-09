# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Restores a Compute Disk Backup."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.backupdr.backups import BackupsClient
from googlecloudsdk.api_lib.backupdr.backups import DiskRestoreConfig
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.command_lib.backupdr.restore import disk_flags
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Disk(base.Command):
  """Restores a Compute Disk Backup."""

  detailed_help = {
      'BRIEF': 'Restores the specified backup',
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
        To restore a backup `sample-backup` in project `sample-project` and location `us-central1`,
        with `sample-data-store` and `sample-backup-vault`, and additional target properties, run:

          $ {command} sample-backup --project=sample-project --location=us-central1 --backup-vault=sample-backup-vault --data-source=sample-data-source --<target-properties>
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddBackupResourceArg(
        parser, 'The backup of a resource to be restored.'
    )

    disk_flags.AddNameArg(parser)
    disk_flags.AddTargetZoneArg(parser, False)
    disk_flags.AddTargetRegionArg(parser, False)
    disk_flags.AddTargetProjectArg(parser)

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """
    client = BackupsClient()
    is_async = args.async_

    backup = args.CONCEPTS.backup.Parse()
    restore_config = DiskRestoreConfig()
    restore_config['Name'] = args.name
    restore_config['TargetProject'] = args.target_project
    if args.target_zone:
      restore_config['TargetZone'] = args.target_zone
    if args.target_region:
      restore_config['TargetRegion'] = args.target_region
    try:
      operation = client.RestoreDisk(backup, restore_config)
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT) from e

    if is_async:
      log.RestoredResource(
          backup.Name(),
          kind='backup',
          is_async=True,
          details=util.ASYNC_OPERATION_MESSAGE.format(operation.name),
      )
      return operation

    # For sync operation
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'Restoring backup'
            ' [{}].'
            ' (This operation could take upto 15 minutes.)'.format(
                backup.Name()
            )
        ),
        has_result=False,
    )
