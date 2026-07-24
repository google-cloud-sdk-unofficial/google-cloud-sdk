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
"""Command for omnichannel-gateway routes create."""

from googlecloudsdk.api_lib.agentic_applications import client as api_client
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.agentic_applications import util as agentic_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class Create(base.CreateCommand):
  """Create an omnichannel route."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    parser.add_argument(
        'route_id',
        nargs='?',
        help=(
            'ID of the route to create. If not specified, a'
            ' unique ID will be generated.'
        ),
    )
    concept_parsers.ConceptParser.ForResource(
        '--location',
        agentic_utils.GetLocationResourceSpec(
            help_text='Location/Region of the route.'
        ),
        'Location/Region of the route.',
        required=True,
    ).AddToParser(parser)
    parser.add_argument(
        '--route-config',
        required=True,
        type=arg_parsers.ArgJSON(),
        metavar='ROUTE_CONFIG',
        help='The route configuration to create.',
    )
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat('yaml')

  def Run(self, args):
    """Run routes create command."""
    location_ref = args.CONCEPTS.location.Parse()
    project = location_ref.projectsId
    location = location_ref.locationsId
    route_id = args.route_id
    route_body = args.route_config

    url = agentic_utils.GetRoutesUrl(project, location)

    # In AIP-133 standard REST, POST creation parameters are passed as
    # query fields.
    params = {}
    if route_id:
      params['routeId'] = route_id

    client = api_client.OmnichannelGatewayClient()
    operation = client.Request(
        'POST',
        url,
        body=route_body,
        params=params,
        error_msg='Failed to create route',
    )

    if args.async_:
      return operation

    return agentic_utils.WaitForOperation(
        operation,
        client.session,
        'Waiting for omnichannel route to be created',
    )
