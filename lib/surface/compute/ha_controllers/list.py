# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""List Compute Engine HA Controllers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base

RESOURCE_TYPE = 'HA Controllers'

DETAILED_HELP = {
    'brief':
        'List Compute Engine ' + RESOURCE_TYPE,
    'DESCRIPTION':
        """\
          *{{command}}* displays all Compute Engine {0} in a project.
        """.format(RESOURCE_TYPE)
}

EXAMPLE_FORMAT = """\
          To list all {0} in a project in table form, run:

            $ {{command}}

      To list {0} in specific regions only in table form, run:

            $ {{command}} --regions=REGION1,REGION2...

      To list the URIs of all {0} in a project, run:

            $ {{command}} --uri
    """


def _TransformSecondaryZone(resource):
  """Returns the secondary zone for the HA Controller."""
  if (
      not resource
      or not resource.get('status')
      or not resource['status'].get('zoneStatus')
  ):
    return ''
  for zone, config in resource['status']['zoneStatus'].items():
    if not config['isPrimary']:
      return zone


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Compute Engine HA Controllers."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
      table(
        name,
        region.basename(),
        status.primaryZone,
        secondaryZone(),
        instanceName,
        status.ongoingFailover,
        failoverInitiation,
        secondaryZoneCapacity
      )""")
    parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
    parser.display_info.AddTransforms({
        'secondaryZone': _TransformSecondaryZone,
    })
    lister.AddRegionsArg(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseRegionalFlags(args, holder.resources)

    list_implementation = lister.RegionalLister(
        client, client.apitools_client.haControllers
    )

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = DETAILED_HELP.copy()
List.detailed_help['EXAMPLES'] = EXAMPLE_FORMAT.format(RESOURCE_TYPE)
