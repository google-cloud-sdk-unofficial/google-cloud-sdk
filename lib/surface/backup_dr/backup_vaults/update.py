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
"""Updates a Backup and DR Backup Vault."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.backupdr.backup_vaults import BackupVaultsClient
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.command_lib.backupdr import util as command_util
from googlecloudsdk.core import log


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """Update a Backup and DR backup vault."""

  detailed_help = {
      'BRIEF': 'Updates a Backup and DR backup vault.',
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
        To update a backup vault BACKUP_VAULT in location MY_LOCATION with one update field, run:

        $ {command} BACKUP_VAULT --location=MY_LOCATION --effective-time="2024-03-22"

        To update a backup vault BACKUP_VAULT in location MY_LOCATION with multiple update fields, run:

        $ {command} BACKUP_VAULT --location=MY_LOCATION --enforced-retention="400000s" --description="Updated backup vault"
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    flags.AddBackupVaultResourceArg(
        parser,
        'Name of the existing backup vault to update.',
    )
    flags.AddNoAsyncFlag(parser)
    flags.AddEnforcedRetention(parser, False)
    flags.AddDescription(parser)
    flags.AddEffectiveTime(parser)
    flags.AddUnlockEnforcedRetention(parser)

  def GetUpdateMask(self, args):
    updated_fields = []
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if args.IsSpecified('enforced_retention'):
      updated_fields.append('enforcedRetentionDuration')
    if args.IsSpecified('unlock_enforced_retention') or args.IsSpecified(
        'effective_time'
    ):
      updated_fields.append('effectiveTime')
    return ','.join(updated_fields)

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """
    client = BackupVaultsClient()
    backup_vault = args.CONCEPTS.backup_vault.Parse()

    enforced_retention = command_util.ConvertIntToStr(args.enforced_retention)
    description = args.description
    if args.unlock_enforced_retention:
      effective_time = command_util.ResetEnforcedRetention()
    else:
      effective_time = command_util.TransformTo12AmUtcTime(args.effective_time)
    no_async = args.no_async

    try:
      parsed_bv = client.ParseUpdate(
          description=description,
          enforced_retention=enforced_retention,
          effective_time=effective_time,
      )

      update_mask = self.GetUpdateMask(args)
      operation = client.Update(
          backup_vault,
          parsed_bv,
          update_mask=update_mask,
      )

    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT)

    if no_async:
      resource = client.WaitForOperation(
          operation_ref=client.GetOperationRef(operation),
          message=(
              'Updating backup vault [{}]. (This operation could'
              ' take up to 1 minute.)'.format(backup_vault.RelativeName())
          ),
          has_result=False,
      )
      log.UpdatedResource(backup_vault.RelativeName(), kind='backup vault')
      return resource

    log.UpdatedResource(
        operation.name,
        kind='backup vault',
        is_async=True,
        details=(
            'Run the [gcloud backup-dr operations describe] command '
            'to check the status of this operation.'
        ),
    )
    return operation
