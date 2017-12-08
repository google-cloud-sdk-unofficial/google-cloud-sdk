# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Deletes a backup run for a Cloud SQL instance."""

import sys

from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(base.DeleteCommand):
  """Delete a backup of a Cloud SQL instance."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'id',
        type=arg_parsers.BoundedInt(1, sys.maxint),
        help="""The ID of the backup run. You can find the ID by running
            $ gcloud beta sql backups list.""")
    flags.INSTANCE_FLAG.AddToParser(parser)

  def Run(self, args):
    """Deletes a backup of a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the delete
      operation if the api request was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']
    operation_ref = None

    validate.ValidateInstanceName(args.instance)
    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    # TODO(user): validate on FE that a backup run id is valid.

    console_io.PromptContinue(
        message='The backup will be deleted. You cannot undo this action.',
        default=True,
        cancel_on_no=True)

    result = sql_client.backupRuns.Delete(
        sql_messages.SqlBackupRunsDeleteRequest(
            project=instance_ref.project,
            instance=instance_ref.instance,
            id=args.id))

    operation_ref = resources.Create(
        'sql.operations',
        operation=result.name,
        project=instance_ref.project,
        instance=instance_ref.instance,
    )

    operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                  'Deleting backup run')

    log.DeletedResource(args.id, 'backup run')
