# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Command for listing spokes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.network_connectivity import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
class QueryStatus(base.ListCommand):
  """Query the status of Private Service Connect propagation for a hub."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    # Remove URI flag to match surface spec
    base.URI_FLAG.RemoveFromParser(parser)
    flags.AddHubResourceArg(
        parser, """to query Private Service Connect propagation for"""
    )
    # TODO(b/347697136): remove list of values and instead link to documentation
    parser.add_argument(
        '--group-by',
        help="""
        Comma-separated list of resource field key names to group by. Aggregated
        values will be displayed for each group. If `--group-by` is set, the value
        of the `--sort-by` flag must be the same as or a subset of the `--group-by`
        flag.

        Accepted values are:
        - 'psc_propagation_status.source_spoke'
        - 'psc_propagation_status.source_group'
        - 'psc_propagation_status.source_forwarding_rule'
        - 'psc_propagation_status.target_spoke'
        - 'psc_propagation_status.target_group'
        - 'psc_propagation_status.code'
        """,
    )
    parser.display_info.AddFormat("""
      table(
        pscPropagationStatus.sourceForwardingRule.basename(),
        pscPropagationStatus.sourceSpoke.basename(),
        pscPropagationStatus.sourceGroup.basename(),
        pscPropagationStatus.targetSpoke.basename(),
        pscPropagationStatus.targetGroup.basename(),
        pscPropagationStatus.code:label=CODE,
        pscPropagationStatus.message:label=MESSAGE,
        count)
        """)

  def Run(self, args):
    release_track = self.ReleaseTrack()
    client = networkconnectivity_api.HubsClient(release_track)
    hub_ref = args.CONCEPTS.hub.Parse()

    sort_by_string = ''
    if args.sort_by:
      sort_by_string = ','.join(args.sort_by)

    return client.QueryHubStatus(
        hub_ref,
        filter_expression=args.filter,
        group_by=args.group_by,
        order_by=sort_by_string,
        page_size=args.page_size,
        limit=args.limit,
    )

QueryStatus.detailed_help = {
    'EXAMPLES': """ \
  To query the Private Service Connect propagation status of a hub, run:

        $ {command} HUB

  To query the Private Service Connect propagation status of a hub grouped by source spoke and code, run:

        $ {command} HUB --group-by="psc_propagation_status.source_spoke,psc_propagation_status.code"

  To query the Private Service Connect propagation status of a hub sorted by the source forwarding rule, run:

        $ {command} HUB --sort-by="psc_propagation_status.source_forwarding_rule"

  """,
    'API REFERENCE': """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
