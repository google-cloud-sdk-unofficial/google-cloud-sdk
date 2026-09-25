# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command to list App Topology locations."""

from googlecloudsdk.api_lib.app_topology import locations as locations_api
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties

_FORMAT = """
  table(
    locationId:label=LOCATION_ID,
    name:label=NAME
  )
"""


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class List(base.ListCommand):
  """List App Topology locations.

  Lists the Google Cloud locations/regions where the App Topology service is
  available.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': (
          """\
          To list all available locations for the current project:

            $ {command}

          To list all locations with their full resource URIs:

            $ {command} --uri
          """
      ),
  }

  @staticmethod
  def Args(parser):
    """Registers command-line flags and arguments for locations list."""
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(lambda r: r.name)

  def Run(self, args):
    """Executes the locations list command.

    Args:
      args: argparse.Namespace, The parsed command-line arguments.

    Returns:
      Generator: Yields Location messages.
    """
    client = locations_api.LocationsClient()
    project = properties.VALUES.core.project.Get(required=True)
    # Normalize project ID to format 'projects/{project}'.
    if not project.startswith('projects/'):
      parent = f'projects/{project}'
    else:
      parent = project
    return client.List(
        parent=parent, page_size=args.page_size, limit=args.limit
    )
