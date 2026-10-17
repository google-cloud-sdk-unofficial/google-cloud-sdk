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
"""gcloud dns outbound-endpoints list command."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import resource_args


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  r"""Lists Cloud DNS outbound endpoints in a region.

  This command lists all Cloud DNS outbound endpoints in a specified region.

  ## EXAMPLES

  To list all outbound endpoints in `us-east1`, run:

    $ {command} --location=us-east1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(
        parser, verb='to list outbound endpoints in', api_version='v1'
    )
    parser.display_info.AddFormat("""
        table(
            name.basename():label=NAME,
            endpointIp:label=ENDPOINT_IP,
            network.basename():label=NETWORK,
            subnetwork.basename():label=SUBNETWORK,
            description:label=DESCRIPTION
        )
    """)

  def Run(self, args):
    api_version = 'v1'
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    location_ref = args.CONCEPTS.location.Parse()
    request = messages.DnsOutboundEndpointsListRequest(
        parent=location_ref.RelativeName()
    )
    return list_pager.YieldFromList(
        client.outboundEndpoints,
        request,
        limit=args.limit,
        field='outboundEndpoints',
        batch_size_attribute='pageSize',
    )
