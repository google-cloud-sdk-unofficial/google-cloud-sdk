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

"""List all instance operations.

Lists all instance operations that have been performed on the given
Cloud SQL instance.
"""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.sql import errors
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags


class _BaseList(object):
  """Base class for sql list operations."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.INSTANCE_FLAG.AddToParser(parser)

  @errors.ReraiseHttpException
  def Run(self, args):
    """Lists all instance operations that have been performed on an instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object that has the list of operation resources if the command ran
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
        sql_client.operations,
        sql_messages.SqlOperationsListRequest(
            project=instance_ref.project,
            instance=instance_ref.instance),
        limit=args.limit)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(_BaseList, base.ListCommand):
  """Lists all instance operations for the given Cloud SQL instance."""

  def Collection(self):
    return 'sql.operations'


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(_BaseList, base.ListCommand):
  """Lists all instance operations for the given Cloud SQL instance."""

  def Collection(self):
    return 'sql.operations.v1beta4'
