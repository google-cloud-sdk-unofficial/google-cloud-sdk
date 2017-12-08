# Copyright 2016 Google Inc. All Rights Reserved.
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

"""The runtime-configs variables list command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.deployment_manager.runtime_configs import util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deployment_manager.runtime_configs import flags


class List(base.ListCommand):
  """List variable resources within a configuration.

  This command lists the variable resources within a specified configuration.
  """

  DEFAULT_PAGE_SIZE = 100

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To list all variables within the configuration named "my-config", run:

            $ {command} --config-name my-config

          The --filter parameter can be used to filter results based on content.
          For example, to list all variables under the path 'status/', run:

            $ {command} --config-name my-config --filter 'name=status/*'
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
    flags.AddConfigFlag(parser)

  def Collection(self):
    """Returns the default collection path string.

    Returns:
      The default collection path string.
    """
    return 'runtimeconfig.variables'

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Run 'runtime-configs variables list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Yields:
      The list of variables.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    variable_client = util.VariableClient()
    messages = util.Messages()

    config_resource = util.ParseConfigName(util.ConfigName(args))
    project = config_resource.projectsId
    config = config_resource.Name()

    request = messages.RuntimeconfigProjectsConfigsVariablesListRequest(
        projectsId=project,
        configsId=config,
    )

    page_size = args.page_size or self.DEFAULT_PAGE_SIZE

    results = list_pager.YieldFromList(
        variable_client, request, field='variables',
        batch_size_attribute='pageSize', limit=args.limit,
        batch_size=page_size
    )

    for result in results:
      yield util.FormatVariable(result)
