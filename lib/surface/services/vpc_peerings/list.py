# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""services vpc-peerings list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.services import peering
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import properties

_DETAILED_HELP = {
    'DESCRIPTION':
        """\
        This command lists connections of a network to a service via VPC peering
        for a project.
        """,
    'EXAMPLES':
        """\
        To list connections of a network called `my-network` to a service called
        `your-service`, run:

          $ {command} --network my-network --service your-service \\
        """,
}

_SERVICE_HELP = """The service to list connections"""
_NETWORK_HELP = """The network in the current project to list connections
 with the service"""


class List(base.DescribeCommand):
  """List connections to a service via VPC peering for a project network."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        '--network', metavar='NETWORK', required=True, help=_NETWORK_HELP)
    parser.add_argument(
        '--service',
        metavar='SERVICE',
        default='servicenetworking.googleapis.com',
        help=_SERVICE_HELP)

  def Run(self, args):
    """Run 'services vpc-peerings list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of connections.
    """
    project = properties.VALUES.core.project.Get(required=True)
    project_number = _GetProjectNumber(project)
    conns = peering.ListConnections(project_number, args.service, args.network)
    return iter(conns)


List.detailed_help = _DETAILED_HELP


def _GetProjectNumber(project_id):
  return projects_api.Get(projects_util.ParseProject(project_id)).projectNumber
