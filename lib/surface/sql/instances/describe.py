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

"""Retrieves information about a Cloud SQL instance."""

from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base


class _BaseGet(object):
  """Displays configuration and metadata about a Cloud SQL instance."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'instance',
        completion_resource='sql.instances',
        help='Cloud SQL instance ID.')

  def Run(self, args):
    """Displays configuration and metadata about a Cloud SQL instance.

    Information such as instance name, IP address, region, the CA certificate
    and configuration settings will be displayed.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the instance resource if fetching the instance
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

    return sql_client.instances.Get(
        sql_messages.SqlInstancesGetRequest(
            project=instance_ref.project,
            instance=instance_ref.instance))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Get(_BaseGet, base.DescribeCommand):
  """Displays configuration and metadata about a Cloud SQL instance.

  Displays configuration and metadata about a Cloud SQL instance.

  Information such as instance name, IP address, region, the CA certificate
  and configuration settings will be displayed.
  """
  pass


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class GetBeta(_BaseGet, base.DescribeCommand):
  """Displays configuration and metadata about a Cloud SQL instance.

  Displays configuration and metadata about a Cloud SQL instance.

  Information such as instance name, IP address, region, the CA certificate
  and configuration settings will be displayed.
  """
  pass
