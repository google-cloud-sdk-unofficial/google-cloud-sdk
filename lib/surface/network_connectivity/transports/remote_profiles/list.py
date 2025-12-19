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

"""Command for listing remote transport profiles."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.command_lib.network_connectivity import util
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List remote transport profiles.

  Retrieve and display a list of all remote transport profiles in the specified
  project.
  """

  @staticmethod
  def Args(parser):
    # Remove URI flag to match surface spec
    base.URI_FLAG.RemoveFromParser(parser)

    # Add flags to identify region
    flags.AddRegionFlag(
        parser, supports_region_wildcard=True, hidden=False, required=False
    )

    # Table formatting
    parser.display_info.AddFormat(util.LIST_REMOTE_PROFILES_FORMAT)

  def Run(self, args):
    client = networkconnectivity_api.RemoteProfilesClient(
        release_track=self.ReleaseTrack()
    )

    project = properties.VALUES.core.project.GetOrFail()
    return client.List(
        location_ref=f'projects/{project}/locations/{args.region or "-"}',
        limit=args.limit,
        filter_expression=None,  # Do all filtering client-side.
        page_size=args.page_size,
    )


List.detailed_help = {
    'EXAMPLES': """ \
  To list all remote transport profiles in the ``us-central1'' region, run:

        $ {command} --region=us-central1

  To list all remote transport profiles in all regions, run:

        $ {command}
  """,
    'API REFERENCE': """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
