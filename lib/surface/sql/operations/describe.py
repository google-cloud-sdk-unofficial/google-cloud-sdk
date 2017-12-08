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

"""Retrieves information about a Cloud SQL instance operation."""

from googlecloudsdk.api_lib.sql import errors
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags


class _BaseGet(object):
  """Base class for sql get operations."""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Get(_BaseGet, base.DescribeCommand):
  """Retrieves information about a Cloud SQL instance operation."""

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
        help='Name that uniquely identifies the operation.')
    flags.INSTANCE_FLAG.AddToParser(parser)

  @errors.ReraiseHttpException
  def Run(self, args):
    """Retrieves information about a Cloud SQL instance operation.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource if the api request was
      successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    resources = self.context['registry']

    validate.ValidateInstanceName(args.instance)
    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    operation_ref = resources.Parse(
        args.operation, collection='sql.operations',
        params={'project': instance_ref.project,
                'instance': instance_ref.instance})

    result = sql_client.operations.Get(operation_ref.Request())
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class GetBeta(_BaseGet, base.DescribeCommand):
  """Retrieves information about a Cloud SQL instance operation."""

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
        help='Name that uniquely identifies the operation.')

  @errors.ReraiseHttpException
  def Run(self, args):
    """Retrieves information about a Cloud SQL instance operation.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource if the api request was
      successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    resources = self.context['registry']

    operation_ref = resources.Parse(
        args.operation, collection='sql.operations',
        params={'project': args.project})

    result = sql_client.operations.Get(operation_ref.Request())
    return result
