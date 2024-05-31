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
"""Deletes a Backup and DR Backup Vault."""

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
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.DeleteCommand):
  """Create a Backup and DR backup vault."""

  detailed_help = {
      'BRIEF': 'Creates a Backup and DR backup vault.',
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
        To create a new backup vault ``BACKUP_VAULT'' in location ``MY_LOCATION'' with enforced-retention
        of 1 month and 1 day, run:
        $ {command} BACKUP_VAULT --location=MY_LOCATION --enforced-retention="p1m1d"

        To create a new backup vault ``BACKUP_VAULT'' in location ``MY_LOCATION'' with enforced-retention
        of 1 day and description ``DESCRIPTION'', run:

        $ {command} BACKUP_VAULT --location=MY_LOCATION --enforced-retention="1d" --description=DESCRIPTION

        To create a new backup vault ``BACKUP_VAULT'' in location ``MY_LOCATION'' with enforced-retention
        of 1 day and label key1 with value value1, run:
        $ {command} BACKUP_VAULT --location=MY_LOCATION --enforced-retention="1d" --labels=key1=value1

        To create a new backup vault ``BACKUP_VAULT'' in location ``MY_LOCATION'' with
        enforced-retention of 1 day and effective-time "2024-03-22", run:

        $ {command} BACKUP_VAULT --location=MY_LOCATION --enforced-retention="1d" --effective-time="2024-03-22"
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
        'Name of the backup vault to create.  A vault name cannot be changed'
        ' after creation. It must be between 3-63 characters long and must be'
        ' unique within the project and location.',
    )
    flags.AddNoAsyncFlag(parser)
    flags.AddEnforcedRetention(parser, True)
    flags.AddDescription(parser)
    flags.AddEffectiveTime(parser)
    flags.AddLabels(parser)

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
    effective_time = command_util.TransformTo12AmUtcTime(args.effective_time)
    labels = labels_util.ParseCreateArgs(
        args, client.messages.BackupVault.LabelsValue
    )
    no_async = args.no_async

    try:
      operation = client.Create(
          backup_vault,
          enforced_retention,
          description,
          labels,
          effective_time,
      )
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT)

    if no_async:
      resource = client.WaitForOperation(
          operation_ref=client.GetOperationRef(operation),
          message=(
              'Creating backup vault [{}]. (This operation could'
              ' take up to 2 minutes.)'.format(backup_vault.RelativeName())
          ),
      )
      log.CreatedResource(backup_vault.RelativeName(), kind='backup vault')
      return resource

    log.CreatedResource(
        operation.name,
        kind='backup vault',
        is_async=True,
        details=(
            'Run the [gcloud backup-dr operations describe] command '
            'to check the status of this operation.'
        ),
    )
    return operation
