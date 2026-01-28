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
"""Updates a Backup and DR Backup."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.backupdr.backups import BackupsClient
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.command_lib.backupdr import util as command_util
from googlecloudsdk.core import log


def _add_common_args(parser: argparse.ArgumentParser) -> None:
  """Specifies additional command flags.

  Args:
    parser: argparse.Parser: Parser object for command line inputs.
  """
  base.ASYNC_FLAG.AddToParser(parser)
  base.ASYNC_FLAG.SetDefault(parser, True)
  flags.AddBackupResourceArg(
      parser,
      'Name of the backup to update.',
  )
  flags.AddUpdateBackupFlags(parser)


def _get_update_mask(args) -> str:
  updated_fields = []
  if args.IsSpecified('enforced_retention_end_time'):
    updated_fields.append('enforcedRetentionEndTime')
  if args.IsSpecified('expire_time'):
    updated_fields.append('expireTime')
  label_flags = ['update_labels', 'remove_labels', 'clear_labels']
  if any(args.IsSpecified(flag) for flag in label_flags):
    updated_fields.append('labels')
  return ','.join(updated_fields)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update the specified Backup."""

  detailed_help = {
      'BRIEF': 'Updates a specific backup',
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
        To update the enforced retention of a backup sample-backup in backup vault sample-vault, data source
        sample-ds, project sample-project and location us-central1, run:

          $ {command} sample-backup --backup-vault=sample-vault --data-source=sample-ds --project=sample-project --location=us-central1 --enforced-retention-end-time="2025-02-14T01:10:20Z"

        To update the labels on a backup named `my-backup` in the `test-bv` vault and `us-central1` location, run:

            $ {command} my-backup --backup-vault=test-bv --location=us-central1 --update-labels=env=prod,team=storage

        To remove the `env` label from the same backup, run:

            $ {command} my-backup --backup-vault=test-bv --location=us-central1 --remove-labels=env

        To clear all labels from the backup, run:

            $ {command} my-backup --backup-vault=test-bv --location=us-central1 --clear-labels
        """,
  }

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    _add_common_args(parser)

  def ParseUpdate(self, backup, args, client):
    updated_enforced_retention = command_util.VerifyDateInFuture(
        args.enforced_retention_end_time, 'enforced-retention-end-time'
    )

    expire_time = command_util.VerifyDateInFuture(
        args.expire_time, 'expire-time'
    )

    return client.ParseUpdate(
        backup,
        updated_enforced_retention,
        expire_time,
        args.update_labels,
        args.remove_labels,
        args.clear_labels,
    )

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

    label_flags = ['update_labels', 'remove_labels', 'clear_labels']
    has_label_flag = any(args.IsSpecified(flag) for flag in label_flags)
    has_enforced_retention = args.IsSpecified('enforced_retention_end_time')
    has_expire_time = args.IsSpecified('expire_time')
    has_time_flag = has_enforced_retention or has_expire_time

    if not (has_label_flag or has_time_flag):
      raise calliope_exceptions.RequiredArgumentException(
          '--update-labels | --remove-labels | --clear-labels | '
          '(--enforced-retention-end-time | --expire-time)',
          'At least one of the update flags must be provided.',
      )

    try:
      parsed_backup = self.ParseUpdate(backup, args, client)

      update_mask = _get_update_mask(args)

      operation = client.Update(
          backup,
          parsed_backup,
          update_mask=update_mask,
      )
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT)

    if is_async:
      log.UpdatedResource(
          backup.RelativeName(),
          kind='backup',
          is_async=True,
          details=util.ASYNC_OPERATION_MESSAGE.format(operation.name),
      )
      return operation

    response = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'Updating backup [{}]. (This operation usually takes less than 1'
            ' minute.)'.format(backup.RelativeName())
        ),
        has_result=False,
    )
    log.UpdatedResource(backup.RelativeName(), kind='backup')

    return response


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update the specified Backup."""

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    _add_common_args(parser)

  def ParseUpdate(self, backup, args, client):
    updated_enforced_retention = command_util.VerifyDateInFuture(
        args.enforced_retention_end_time, 'enforced-retention-end-time'
    )

    expire_time = command_util.VerifyDateInFuture(
        args.expire_time, 'expire-time'
    )

    return client.ParseUpdate(
        backup,
        updated_enforced_retention,
        expire_time,
        args.update_labels,
        args.remove_labels,
        args.clear_labels,
    )

  def GetUpdateMask(self, args):
    return _get_update_mask(args)
