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

"""operations list command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List types in a project.

  Prints a a list of the available resource types.
  """

  detailed_help = {
      'EXAMPLES': """\
          To print out a list of all available type names, run:

            $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    base.FLATTEN_FLAG.RemoveFromParser(parser)
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """Run 'types list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of types for this project.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    client = self.context['deploymentmanager-client']
    messages = self.context['deploymentmanager-messages']
    project = properties.VALUES.core.project.Get(required=True)

    request = messages.DeploymentmanagerTypesListRequest(project=project)
    return dm_v2_util.YieldWithHttpExceptions(
        list_pager.YieldFromList(client.types, request, field='types',
                                 batch_size=args.page_size, limit=args.limit))

  def Format(self, unused_args):
    return 'value(name)'

  def Epilog(self, resources_were_displayed):
    if not resources_were_displayed:
      log.status.Print('No types were found for your project!')
