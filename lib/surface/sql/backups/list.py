# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Lists all backups associated with a given instance.

Lists all backups associated with a given instance and configuration
in the reverse chronological order of the enqueued time.
"""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags


class _BaseList(object):
  """Base class for sql backups list."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.INSTANCE_FLAG.AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(_BaseList, base.ListCommand):
  """Lists all backups associated with a given instance.

  Lists all backups associated with a given Cloud SQL instance and
  configuration in the reverse chronological order of the enqueued time.
  """

  def Collection(self):
    return 'sql.backupRuns'

  def Run(self, args):
    """Lists all backups associated with a given instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object that has the list of backup run resources if the command ran
      successfully.
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

    instance_resource = sql_client.instances.Get(
        sql_messages.SqlInstancesGetRequest(
            project=instance_ref.project,
            instance=instance_ref.instance))
    config_id = instance_resource.settings.backupConfiguration[0].id

    return list_pager.YieldFromList(
        sql_client.backupRuns,
        sql_messages.SqlBackupRunsListRequest(
            project=instance_ref.project,
            instance=instance_ref.instance,
            # At this point we support only one backup-config. So, we just use
            # that id.
            backupConfiguration=config_id),
        limit=args.limit)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(_BaseList, base.ListCommand):
  """Lists all backups associated with a given instance.

  Lists all backups associated with a given Cloud SQL instance and
  configuration in the reverse chronological order of the enqueued time.
  """

  def Collection(self):
    return 'sql.backupRuns.v1beta4'

  def Run(self, args):
    """Lists all backups associated with a given instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object that has the list of backup run resources if the command ran
      successfully.
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

    return list_pager.YieldFromList(
        sql_client.backupRuns,
        sql_messages.SqlBackupRunsListRequest(
            project=instance_ref.project,
            instance=instance_ref.instance),
        limit=args.limit)
