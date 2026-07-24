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
"""The list command for omnichannel-gateway endpoint-configs."""

from googlecloudsdk.api_lib.agentic_applications import client as api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.agentic_applications import util
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def _GetUri(endpoint):
  """Returns the URI for an omnichannel endpoint configuration."""
  name = endpoint.get('name', '')
  api_endpoint = util.GetApiEndpoint()
  return f'https://{api_endpoint}/v1alpha/{name}'


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class List(base.ListCommand):
  """List omnichannel endpoint configurations."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    concept_parsers.ConceptParser.ForResource(
        '--location',
        util.GetLocationResourceSpec(),
        'Location/Region of the endpoint configurations.',
        required=True,
    ).AddToParser(parser)
    parser.display_info.AddFormat("""
          table(
            name.basename():label=ID:sort=1,
            displayName:label=DISPLAY_NAME,
            createTime:label=CREATE_TIME
          )
    """)
    parser.display_info.AddUriFunc(_GetUri)

  def Run(self, args):
    """Run endpoint-configs list command."""
    location_ref = args.CONCEPTS.location.Parse()
    project = location_ref.projectsId
    location = location_ref.locationsId

    url = util.GetEndpointConfigsUrl(project, location)
    client = api_client.OmnichannelGatewayClient()
    data = client.Request(
        'GET', url, error_msg='Failed to list endpoint configs'
    )
    return data.get('omnichannelEndpointConfigs', [])
