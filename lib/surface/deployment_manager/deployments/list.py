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

"""deployments list command."""

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import list_printer
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.third_party.apitools.base.py import list_pager


class List(base.Command):
  """List deployments in a project.

  Prints a table with summary information on all deployments in the project.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To print out a list of deployments with some summary information about each, run:

            $ {command}

          To print only the name of each deployment, run:

            $ {command} --simple-list
          """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('--limit',
                        type=int,
                        help='The maximum number of results to list.')
    parser.add_argument(
        '--simple-list',
        action='store_true',
        default=False,
        help='If true, only the list of resource IDs is printed. If false, '
        'prints a human-readable table of resource information.')

  def Run(self, args):
    """Run 'deployments list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of deployments for this project.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    client = self.context['deploymentmanager-client']
    messages = self.context['deploymentmanager-messages']
    project = properties.VALUES.core.project.Get(required=True)

    request = messages.DeploymentmanagerDeploymentsListRequest(
        project=project,
    )
    return dm_v2_util.YieldWithHttpExceptions(list_pager.YieldFromList(
        client.deployments, request, field='deployments', limit=args.limit,
        batch_size=500))

  def Display(self, args, result):
    """Display prints information about what just happened to stdout.

    Args:
      args: The same as the args in Run.

      result: a generator of Deployment objects.

    Raises:
      ValueError: if result is None or not a generator
    """
    if args.simple_list:
      empty_generator = True
      for deployment in result:
        empty_generator = False
        log.Print(deployment.name)
      if empty_generator:
        log.Print('No Deployments were found in your project!')
    else:
      list_printer.PrintResourceList('deploymentmanagerv2.deployments', result)
