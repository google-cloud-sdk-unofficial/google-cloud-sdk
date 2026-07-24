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
"""Command for omnichannel-gateway onboard-social."""

import urllib.parse

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.agentic_applications import util as agentic_utils
from googlecloudsdk.command_lib.app import browser_dispatcher
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log

PORTAL_URL = 'https://omnichannel.static.usercontent.goog/onboard.html'


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class OnboardSocial(base.Command):
  """Onboard a social channel (Instagram or WhatsApp) via Meta authentication flow."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    concept_parsers.ConceptParser.ForResource(
        '--location',
        agentic_utils.GetLocationResourceSpec(),
        'Location/Region of the endpoint configuration.',
        required=True,
    ).AddToParser(parser)
    parser.add_argument(
        '--type',
        required=True,
        choices=['instagram', 'whatsapp'],
        type=str.lower,
        help='The social channel type to onboard (instagram or whatsapp).',
    )
    parser.display_info.AddFormat('none')

  def Run(self, args):
    """Run onboard-social command."""
    location_ref = args.CONCEPTS.location.Parse()
    project = location_ref.projectsId
    location = location_ref.locationsId
    channel_type = args.type

    query_params = [
        ('projectId', project),
        ('channel', channel_type),
        ('region', location),
    ]

    url = '{base_url}?{query}'.format(
        base_url=PORTAL_URL,
        query=urllib.parse.urlencode(query_params),
    )

    log.status.Print(
        'Opening the onboarding portal in your browser:\n  {url}\n\nPlease'
        ' follow the on-screen directions in the browser to complete Meta'
        ' authentication and execute the generated command in your terminal.'
        .format(url=url)
    )
    browser_dispatcher.OpenURL(url)
    return {
        'url': url,
        'location': location,
        'project': project,
        'type': channel_type,
    }
