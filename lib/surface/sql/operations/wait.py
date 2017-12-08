# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Retrieves information about a Cloud SQL instance operation."""

from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags


class _BaseWait(object):
  """Base class for sql wait operations."""

  def Format(self, args):
    return self.ListFormat(args)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Wait(_BaseWait, base.Command):
  """Waits for one or more operations to complete."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'operation',
        nargs='+',
        help='An identifier that uniquely identifies the operation.')
    flags.INSTANCE_FLAG.AddToParser(parser)

  def Collection(self):
    return 'sql.operations'

  def Run(self, args):
    """Wait for a Cloud SQL instance operation.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Yields:
      Operations that were waited for.
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

    for op in args.operation:
      operation_ref = resources.Parse(
          op, collection='sql.operations',
          params={'project': instance_ref.project,
                  'instance': instance_ref.instance})

      operations.OperationsV1Beta3.WaitForOperation(
          sql_client, operation_ref,
          'Waiting for [{operation}]'.format(operation=operation_ref))
      yield sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project,
              instance=operation_ref.instance,
              operation=operation_ref.operation))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class WaitBeta(_BaseWait, base.Command):
  """Waits for one or more operations to complete."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'operation',
        nargs='+',
        help='An identifier that uniquely identifies the operation.')

  def Collection(self):
    return 'sql.operations.v1beta4'

  def Run(self, args):
    """Wait for a Cloud SQL instance operation.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Yields:
      Operations that were waited for.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']

    for op in args.operation:
      operation_ref = resources.Parse(
          op, collection='sql.operations',
          params={'project': args.project})

      operations.OperationsV1Beta4.WaitForOperation(
          sql_client, operation_ref,
          'Waiting for [{operation}]'.format(operation=operation_ref))
      yield sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project,
              operation=operation_ref.operation))
