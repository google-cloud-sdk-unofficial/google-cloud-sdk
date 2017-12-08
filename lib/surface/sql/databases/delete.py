# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Deletes a database in a given instance."""

from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class _BaseDelete(object):
  """Deletes a Cloud SQL database."""

  def Collection(self):
    return 'sql.databases'

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.INSTANCE_FLAG.AddToParser(parser)
    flags.DATABASE_NAME_FLAG.AddToParser(parser)

  def Run(self, args):
    """Deletes a Cloud SQL database.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      SQL database resource iterator.
    Raises:
      HttpException: An http error response was received while executing api
          request.
      ToolException: An error other than an http error occured while executing
          the command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']

    project_id = properties.VALUES.core.project.Get(required=True)

    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    console_io.PromptContinue(
        message='The database will be deleted. Any data stored in the database '
        'will be destroyed. You cannot undo this action.',
        default=True,
        cancel_on_no=True)

    result_operation = sql_client.databases.Delete(
        sql_messages.SqlDatabasesDeleteRequest(
            project=project_id, instance=args.instance, database=args.database))

    operation_ref = resources.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project,
        instance=instance_ref.instance,)

    operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                  'Deleting Cloud SQL database')
    log.DeletedResource(args.database, 'database')


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(_BaseDelete, base.DeleteCommand):
  """Deletes a Cloud SQL database."""
  pass
