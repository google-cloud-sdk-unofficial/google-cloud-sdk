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

"""Command for describing transports."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a transport.

  Retrieve and display details about a transport.
  """

  @staticmethod
  def Args(parser):
    flags.AddTransportResourceArg(parser, 'to describe')
    flags.AddRegionFlag(
        parser, supports_region_wildcard=True, hidden=False, required=True
    )

  def Run(self, args):
    client = networkconnectivity_api.TransportsClient(
        release_track=self.ReleaseTrack()
    )
    transport_ref = args.CONCEPTS.transport.Parse()
    return client.Get(transport_ref)


Describe.detailed_help = {
    'EXAMPLES': """ \
  To display details about a transport named ``mytransport'' in the ``us-central1'' region, run:

    $ {command} mytransport --region=us-central1
  """,
    'API REFERENCE': """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
