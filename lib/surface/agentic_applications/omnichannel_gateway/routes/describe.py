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
"""Command for omnichannel-gateway routes describe."""

from googlecloudsdk.api_lib.agentic_applications import client as api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.agentic_applications import util as agentic_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class Describe(base.DescribeCommand):
  """Describe an omnichannel route.

  ## EXAMPLES
  To describe a route with ID `my-route` in location `us`, run:

    $ {command} my-route --location=us
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    parser.add_argument(
        'route_id',
        help='ID of the route to describe.',
    )
    concept_parsers.ConceptParser.ForResource(
        '--location',
        agentic_utils.GetLocationResourceSpec('Location/Region of the route.'),
        'Location/Region of the route.',
        required=True,
    ).AddToParser(parser)

  def Run(self, args):
    """Run routes describe command."""
    location_ref = args.CONCEPTS.location.Parse()
    project = location_ref.projectsId
    location = location_ref.locationsId
    route_id = args.route_id

    url = agentic_utils.GetRoutesUrl(project, location, route_id)

    client = api_client.OmnichannelGatewayClient()
    return client.Request(
        'GET', url, error_msg='Failed to describe route'
    )
