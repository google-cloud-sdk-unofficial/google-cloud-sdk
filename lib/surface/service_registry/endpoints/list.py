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

"""'endpoints list' command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.service_registry import constants
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List endpoints for a project.

  This command lists endpoint entries in Service Registry.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To print out a list of endpoints with some summary information about each

            $ {command}

          To limit the number of endpoints returned

            $ {command} --limit=100
          """,
  }

  @staticmethod
  def Args(parser):
    """Called by calliope to gather arguments for this command.

    base.ListCommand provides basic limit, sort, and filter.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    pass

  def Run(self, args):
    """Runs 'endpoints list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      Endpoints for the specified project.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    client = self.context[constants.CLIENT]
    messages = self.context[constants.MESSAGES]
    project = properties.VALUES.core.project.Get(required=True)

    request = messages.ServiceregistryEndpointsListRequest(project=project,)
    return list_pager.YieldFromList(
        client.endpoints, request, field='endpoints', limit=args.limit,
        batch_size=500)

  def Collection(self):
    """Choose the default resource collection key used to list Endpoints.

    Returns:
      A collection string used as a key to select the default ResourceInfo
      from core.resources.resource_registry.RESOURCE_REGISTRY.
    """
    return 'service_registry.endpoints'
