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

"""Command for creating transports."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import textwrap

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Create(base.Command):
  """Create a new Transport.

  Create a new Transport.
  """

  @staticmethod
  def Args(parser):
    flags.AddTransportResourceArg(parser, 'to create')
    flags.AddProfileFlag(parser, 'Profile of the transport to create.')
    flags.AddBandwidthFlag(parser, 'Bandwidth of the transport to create.')
    flags.AddNetworkFlag(parser)
    flags.AddAdvertisedRoutesFlag(
        parser, 'List of routes to advertise to the remote network.'
    )
    flags.AddDescriptionFlag(parser, 'Description of the transport to create.')
    flags.AddEnableAdminFlag(
        parser, 'Administrative state of the underlying connectivity.'
    )
    flags.AddStackTypeFlag(
        parser, 'IP version stack for the established connectivity.'
    )
    flags.AddAsyncFlag(parser)
    flags.AddActivationKeyFlag(
        parser,
        'Key used for establishing a connection with the remote transport.',
    )
    flags.AddRemoteAccountIdFlag(
        parser,
        'The user supplied account id for the CSP associated with the remote'
        ' profile.',
    )
    flags.AddRegionFlag(
        parser, supports_region_wildcard=True, hidden=False, required=True
    )
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args: argparse.Namespace, client=None):
    if client is None:
      client = networkconnectivity_api.TransportsClient(
          release_track=self.ReleaseTrack()
      )

    transport_ref = args.CONCEPTS.transport.Parse()

    labels = labels_util.ParseCreateArgs(
        args,
        client.messages.TransportsV1BetaTransport.LabelsValue,
    )

    transport = client.messages.TransportsV1BetaTransport(
        remoteProfile=args.remote_profile,
        bandwidth=client.messages.TransportsV1BetaTransport.BandwidthValueValuesEnum(
            f'BPS_{args.bandwidth}'
        ),
        network=args.network,
        advertisedRoutes=args.advertised_routes.split(','),
        adminEnabled=args.enable_admin or False,
        stackType=client.messages.TransportsV1BetaTransport.StackTypeValueValuesEnum(
            args.stack_type
        ),
        description=args.description,
        labels=labels,
        providedActivationKey=args.activation_key,
        remoteAccountId=args.remote_account_id,
    )
    op_ref = client.CreateBeta(transport_ref, transport)
    log.status.Print(f'Create request issued for: [{transport_ref.Name()}]')

    if op_ref.done:
      log.CreatedResource(transport_ref.Name(), kind='transport')
      return op_ref

    if args.async_:
      log.status.Print(f'Check operation [{op_ref.name}] for status.')
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='networkconnectivity.projects.locations.operations',
        api_version=networkconnectivity_util.VERSION_MAP[self.ReleaseTrack()],
    )
    poller = waiter.CloudOperationPoller(
        client.transport_service, client.operation_service
    )
    res = waiter.WaitFor(
        poller,
        op_resource,
        f'Waiting for operation [{op_ref.name}] to complete',
    )
    log.CreatedResource(transport_ref.Name(), kind='transport')
    return res


Create.detailed_help = {
    'EXAMPLES': textwrap.dedent(""" \
  To create a transport named ``mytransport'', run:

    $ {command} my-cci-aws-1 --bandwidth 1G \
    --profile aws-us-east-1 --network my-network \
    --advertised-routes '10.128.0.0/9'
  """),
    'API REFERENCE': """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
