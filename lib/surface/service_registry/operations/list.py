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

"""'operations list' command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.service_registry import constants
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List Service Registry operations for a project."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To print out a list of operations with some summary information about each, run:

            $ {command}

          To limit the number of operations returned:

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
    """Runs 'operations list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The requested Operations.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    client = self.context[constants.CLIENT]
    messages = self.context[constants.MESSAGES]
    project = properties.VALUES.core.project.Get(required=True)

    request = messages.ServiceregistryOperationsListRequest(project=project,)
    return list_pager.YieldFromList(
        client.operations, request, field='operations', limit=args.limit,
        batch_size=500)

  def Collection(self):
    """Choose the default resource collection key used to list Operations.

    Returns:
      A collection string used as a key to select the default ResourceInfo
      from core.resources.resource_registry.RESOURCE_REGISTRY.
    """
    return 'service_registry.operations'

