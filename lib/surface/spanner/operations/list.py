# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for spanner operations list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import backup_operations
from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.spanner import instance_config_operations
from googlecloudsdk.api_lib.spanner import instance_operations
from googlecloudsdk.api_lib.spanner import instance_partition_operations
from googlecloudsdk.api_lib.spanner import ssd_cache_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.spanner import flags

DETAILED_HELP = {
    'EXAMPLES': textwrap.dedent("""\
        To list Cloud Spanner instance operations for an instance, run:

          $ {command} --instance=my-instance-id --type=INSTANCE

        To list Cloud Spanner backup operations for an instance, run:

          $ {command} --instance=my-instance-id --type=BACKUP

        To list Cloud Spanner database operations for an instance, run:

          $ {command} --instance=my-instance-id --type=DATABASE

        To list Cloud Spanner database operations for a database, run:

          $ {command} --instance=my-instance-id --database=my-database-id --type=DATABASE

        To list Cloud Spanner backup operations for a database, run:

          $ {command} --instance=my-instance-id --database=my-database-id --type=BACKUP

        To list Cloud Spanner backup operations for a backup, run:

          $ {command} --instance=my-instance-id --backup=my-backup-id --type=BACKUP
        """),
}


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List the Cloud Spanner operations."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    flags.AddCommonListArgs(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    if args.instance_config:
      type_filter = (
          instance_config_operations.BuildInstanceConfigOperationTypeFilter(
              args.type))
      return instance_config_operations.List(args.instance_config, type_filter)

    is_database_type = (
        args.type == 'DATABASE_RESTORE' or args.type == 'DATABASE' or
        args.type == 'DATABASE_CREATE' or args.type == 'DATABASE_UPDATE_DDL')

    if args.backup or args.type == 'BACKUP':
      # Update output table for backup operations.
      # pylint:disable=protected-access
      args._GetParser().ai.display_info.AddFormat("""
            table(
              name.basename():label=OPERATION_ID,
              done():label=DONE,
              metadata.'@type'.split('.').slice(-1:).join(),
              metadata.name.split('/').slice(-1:).join():label=BACKUP,
              metadata.database.split('/').slice(-1).join():label=SOURCE_DATABASE,
              metadata.progress.startTime:label=START_TIME,
              metadata.progress.endTime:label=END_TIME
            )
          """)

    if args.type == 'DATABASE_RESTORE':
      # Update output table for restore operations.
      # pylint:disable=protected-access
      args._GetParser().ai.display_info.AddFormat("""
            table(
              name.basename():label=OPERATION_ID,
              done():label=DONE,
              metadata.'@type'.split('.').slice(-1:).join(),
              metadata.name.split('/').slice(-1:).join():label=RESTORED_DATABASE,
              metadata.backupInfo.backup.split('/').slice(-1).join():label=SOURCE_BACKUP,
              metadata.progress.startTime:label=START_TIME,
              metadata.progress.endTime:label=END_TIME
            )
          """)
    elif is_database_type:
      # Update output table for database operations.
      # pylint:disable=protected-access
      args._GetParser().ai.display_info.AddFormat("""
            table(
              name.basename():label=OPERATION_ID,
              metadata.statements.join(sep="\n"),
              done():label=DONE,
              metadata.'@type'.split('.').slice(-1:).join(),
              database().split('/').slice(-1:).join():label=DATABASE_ID
            )
          """)

    # Checks that user only specified either database or backup flag.
    if (args.IsSpecified('database') and args.IsSpecified('backup')):
      raise c_exceptions.InvalidArgumentException(
          '--database or --backup',
          'Must specify either --database or --backup. To search backups for a '
          'specific database, use the --database flag with --type=BACKUP')

    # Checks that the user did not specify the backup flag with the type filter
    # set to a database operation type.
    if (args.IsSpecified('backup') and is_database_type):
      raise c_exceptions.InvalidArgumentException(
          '--backup or --type',
          'The backup flag cannot be used with the type flag set to a '
          'database operation type.')

    if args.type == 'INSTANCE':
      if args.IsSpecified('database'):
        raise c_exceptions.InvalidArgumentException(
            '--database or --type',
            'The `--database` flag cannot be used with `--type=INSTANCE`.')
      if args.IsSpecified('backup'):
        raise c_exceptions.InvalidArgumentException(
            '--backup or --type',
            'The `--backup` flag cannot be used with `--type=INSTANCE`.')

    if args.type == 'BACKUP':
      if args.database:
        db_filter = backup_operations.BuildDatabaseFilter(
            args.instance, args.database)
        return backup_operations.List(args.instance, db_filter)
      if args.backup:
        return backup_operations.ListGeneric(args.instance, args.backup)
      return backup_operations.List(args.instance)

    if is_database_type:
      type_filter = database_operations.BuildDatabaseOperationTypeFilter(
          args.type)
      return database_operations.ListDatabaseOperations(args.instance,
                                                        args.database,
                                                        type_filter)

    if args.backup:
      return backup_operations.ListGeneric(args.instance, args.backup)
    if args.database:
      return database_operations.List(args.instance, args.database)

    return instance_operations.List(args.instance)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaList(List):
  """List the Cloud Spanner operations with ALPHA features."""

  detailed_help = {
      'EXAMPLES': DETAILED_HELP['EXAMPLES'] + textwrap.dedent("""\

        To list Cloud Spanner instance partition operations for an instance partition, run:

          $ {command} --instance=my-instance-id --instance-partition=my-partition-id --type=INSTANCE_PARTITION

        To list Cloud Spanner instance partition operations for an instance, run:

          $ {command} --instance=my-instance-id --type=INSTANCE_PARTITION
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    additional_choices = {
        'DATABASE_CHANGE_QUORUM': (
            'Database change quorum operations are returned for all databases '
            'in the given instance (--instance only) or only those associated '
            'with the given database (--database).'
        ),
        'INSTANCE_PARTITION': (
            'If only the instance is specified (--instance), returns all '
            'instance partition operations associated with instance partitions '
            'in the instance. When an instance partition is specified '
            '(--instance-partition), only the instance partition operations '
            'for the given instance partition are returned. '
        ),
    }

    flags.AddCommonListArgs(parser, additional_choices)
    flags.SsdCache(
        positional=False,
        required=False,
        hidden=True,
        text='For SSD Cache operations, the SSD Cache ID.',
    ).AddToParser(parser)

    flags.InstancePartition(
        positional=False,
        required=False,
        hidden=True,
        text=(
            'For instance partition operations, the name of the instance '
            'partition the operation is executing on.'
        ),
    ).AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    if args.ssd_cache:
      if args.instance:
        raise c_exceptions.InvalidArgumentException(
            '--instance or --ssd-cache',
            'The `--instance` flag cannot be used with `--ssd-cache`.',
        )
      if args.type:
        raise c_exceptions.InvalidArgumentException(
            '--type or --ssd-cache',
            'The `--type` flag cannot be used with `--ssd-cache`.',
        )
      # Update output table for SSD Cache operations.
      # pylint:disable=protected-access
      args._GetParser().ai.display_info.AddFormat("""
          table(
            name.basename():label=OPERATION_ID,
            done():label=DONE,
            metadata.'@type'.split('.').slice(-1:).join(),
            metadata.startTime:label=START_TIME,
            metadata.endTime:label=END_TIME
          )
        """)
      return ssd_cache_operations.List(args.ssd_cache, args.instance_config)

    flags.CheckExclusiveLROFlagsUnderInstance(args)

    if args.type == 'INSTANCE':
      if args.IsSpecified('instance_partition'):
        raise c_exceptions.InvalidArgumentException(
            '--instance-partition or --type',
            'The `--instance-partition` flag cannot be used with'
            ' `--type=INSTANCE`.',
        )

    if args.type == 'INSTANCE_PARTITION':
      # Update output table for instance partition operations.
      # pylint:disable=protected-access
      args.GetDisplayInfo().AddFormat("""
            table(
              name.basename():label=OPERATION_ID,
              done():label=DONE,
              metadata.'@type'.split('.').slice(-1:).join(),
              metadata.instancePartition.name.split('/').slice(-1:).join():label=INSTANCE_PARTITION_ID,
              metadata.startTime:label=START_TIME,
              metadata.endTime:label=END_TIME
            )
          """)
      if args.instance_partition:
        return instance_partition_operations.ListGeneric(
            args.instance, args.instance_partition
        )
      else:
        return instance_partition_operations.List(args.instance)
    return super().Run(args)
