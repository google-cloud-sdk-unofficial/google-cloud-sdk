# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""List endpoints command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.network_security import activation_flags
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION': """
          List firewall endpoints.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To list firewall endpoints in organization ID 1234, run:

            $ {command} --organization=1234

        """,
}

_FORMAT = """\
table(
    name.scope("firewallEndpoints"):label=ID,
    name.scope("locations").segment(0):label=LOCATION,
    state
)
"""

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
class List(base.ListCommand):
  """List Firewall Plus endpoints."""

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(
        activation_flags.MakeGetUriFunc(cls.ReleaseTrack())
    )
    group = parser.add_group(required=False)
    group.add_argument(
        '--organization',
        help='The organization for a list operation',
    )
    if project_scope_supported:
      common_args.ProjectArgument(
          help_text_to_prepend='The project for a list operation'
      ).AddToParser(group)
    activation_flags.AddZoneArg(
        parser, required=False, help_text='The zone for a list operation'
    )

  def Run(self, args):
    # Temporarily separating the org-only scenario from the org+project scenario
    # to make the code clearer. This section will go away once the project
    # scope is in GA.
    project_scope_supported = (
        self.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    if not project_scope_supported:
      return self._ListOrganizationEndpoints(args)

    organization = args.organization
    project = args.project or properties.VALUES.core.project.Get()
    if not organization and not project:
      raise exceptions.RequiredArgumentException(
          'organization or project',
          '--organization or --project flag must be specified.',
      )

    # We check if organization is not specified because we allow both project
    # and organization, and assume organization in this scenario.
    project_scoped = not organization

    client = activation_api.Client(self.ReleaseTrack(), project_scoped)

    zone = args.zone if args.zone else '-'
    if project_scoped:
      parent = 'projects/{}/locations/{}'.format(project, zone)
    else:
      parent = 'organizations/{}/locations/{}'.format(organization, zone)

    return client.ListEndpoints(parent, args.limit, args.page_size)

  def _ListOrganizationEndpoints(self, args):
    if not args.IsSpecified('organization'):
      raise exceptions.RequiredArgumentException(
          'organization',
          '--organization flag must be specified.',
      )
    client = activation_api.Client(self.ReleaseTrack())
    zone = args.zone if args.zone else '-'
    parent = 'organizations/{}/locations/{}'.format(args.organization, zone)
    return client.ListEndpoints(parent, args.limit, args.page_size)


List.detailed_help = DETAILED_HELP
