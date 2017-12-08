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
"""Retrieves information about a Cloud SQL database."""

from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags


class _BaseGet(object):
  """Displays configuration and metadata about a Cloud SQL database."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.DATABASE_NAME_FLAG.AddToParser(parser)
    flags.INSTANCE_FLAG.AddToParser(parser)

  def Run(self, args):
    """Displays configuration and metadata about a Cloud SQL database.

    Information such as database name, charset, and collation will be displayed.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the database resource if fetching the database
      was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']

    validate.ValidateInstanceName(args.instance)
    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    database_request = sql_messages.SqlDatabasesGetRequest(
        project=instance_ref.project,
        instance=instance_ref.instance,
        database=args.database)
    return sql_client.databases.Get(database_request)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class GetBeta(_BaseGet, base.DescribeCommand):
  """Displays configuration and metadata about a Cloud SQL database.

  Information such as database name, charset, and collation will be displayed.
  """
  pass
