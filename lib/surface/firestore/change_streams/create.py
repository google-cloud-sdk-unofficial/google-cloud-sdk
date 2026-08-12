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
"""Command to create a Cloud Firestore ChangeStream."""

from googlecloudsdk.api_lib.firestore import change_streams
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  r"""Create a Cloud Firestore change stream.

  ## EXAMPLES

  To create a database-scoped change stream named `my-stream` in database
  `my-db`:

      $ {command} my-stream --database=my-db --database-scope

  To create a collection-group-scoped change stream named `my-cg-stream` for
  collection group `my-cg` in database `my-db` with a retention period of 1
  day:

      $ {command} my-cg-stream --database=my-db \
          --collection-group-scope=my-cg --retention=1d
  """

  @staticmethod
  def Args(parser):
    flags.AddDatabaseIdFlag(parser, required=False)
    flags.AddChangeStreamIdArg(parser)
    flags.AddRetentionFlag(
        parser,
        default='7d',
        help_text=(
            'The retention period of the change stream (e.g. 1d, 7d). Must be'
            ' between 1 and 7 days, in day granularity. Default is 7d.'
        ),
    )
    scope_group = parser.add_mutually_exclusive_group(required=True)
    scope_group.add_argument(
        '--database-scope',
        action='store_true',
        help='Create a database-scoped change stream.',
    )
    scope_group.add_argument(
        '--collection-group-scope',
        metavar='COLLECTION_GROUP_ID',
        type=str,
        help=(
            'Create a collection-group-scoped change stream for the specified'
            ' collection group (e.g.,'
            ' --collection-group-scope=my-collection-group).'
        ),
    )

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)

    retention_period = None
    if args.retention:
      seconds = args.retention
      if seconds < 86400 or seconds > 604800 or seconds % 86400 != 0:
        raise exceptions.InvalidArgumentException(
            '--retention',
            'Retention period must be between 1 and 7 days, in day'
            ' granularity.',
        )
      retention_period = f'{int(seconds)}s'

    database_scope = args.database_scope
    collection_group_id = args.collection_group_scope

    if collection_group_id is not None and not collection_group_id:
      raise exceptions.InvalidArgumentException(
          '--collection-group-scope',
          'Collection group ID must not be empty.',
      )

    return change_streams.CreateChangeStream(
        project=project,
        database=args.database,
        change_stream_id=args.change_stream,
        retention_period=retention_period,
        database_scope=database_scope,
        collection_group_id=collection_group_id,
    )
