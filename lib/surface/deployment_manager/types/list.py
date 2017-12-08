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

import types

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.third_party.apitools.base.py import list_pager


class List(base.Command):
  """List types in a project.

  Prints a a list of the available resource types.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To print out a list of all available type names, run:

            $ {command}
          """,
  }

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
                                 batch_size=500))

  def Display(self, args, result):
    """Display prints information about what just happened to stdout.

    Args:
      args: The same as the args in Run.

      result: a list of types, where each dict is a Type object with a name
          attribute.

    Raises:
      ValueError: if result is None or not a generator
    """
    if not isinstance(result, types.GeneratorType):
      raise ValueError('result must be a generator')

    empty_generator = True
    for type_item in result:
      empty_generator = False
      log.Print(type_item.name)
    if empty_generator:
      log.Print('No types were found for your project!')
