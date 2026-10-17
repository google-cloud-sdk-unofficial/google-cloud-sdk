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
"""gcloud dns outbound-endpoints create command."""

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.dns import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _FormatNetwork(network: str | None, project: str) -> str | None:
  if not network or '/' in network:
    return network
  return f'projects/{project}/global/networks/{network}'


def _FormatSubnetwork(
    subnetwork: str | None, project: str, location: str
) -> str | None:
  if not subnetwork or '/' in subnetwork:
    return subnetwork
  return f'projects/{project}/regions/{location}/subnetworks/{subnetwork}'


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  r"""Creates a new Cloud DNS outbound endpoint.

  This command creates a new Cloud DNS outbound endpoint in a specified region.

  ## EXAMPLES

  To create a new outbound endpoint `my-endpoint` in `us-east1`, run:

    $ {command} my-endpoint --location=us-east1 \
        --network=projects/my-project/global/networks/my-network \
        --subnetwork=projects/my-project/regions/us-east1/subnetworks/my-subnet \
        --endpoint-ip=10.128.0.5 \
        --description="My outbound endpoint"
  """

  @staticmethod
  def Args(parser):
    resource_args.AddOutboundEndpointResourceArg(
        parser, verb='to create', api_version='v1'
    )
    flags.GetOutboundEndpointNetworkArg(required=True).AddToParser(parser)
    flags.GetOutboundEndpointSubnetworkArg(required=True).AddToParser(parser)
    flags.GetOutboundEndpointIpArg(required=True).AddToParser(parser)
    flags.GetOutboundEndpointDescriptionArg(required=False).AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat('json')

  def Run(self, args):
    api_version = 'v1'
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    endpoint_ref = args.CONCEPTS.outbound_endpoint.Parse()
    endpoint_id = endpoint_ref.Name()
    project = endpoint_ref.projectsId
    location = endpoint_ref.locationsId
    parent = f'projects/{project}/locations/{location}'

    labels = labels_util.ParseCreateArgs(
        args, messages.OutboundEndpoint.LabelsValue
    )

    outbound_endpoint = messages.OutboundEndpoint(
        name=endpoint_ref.RelativeName(),
        network=_FormatNetwork(args.network, project),
        subnetwork=_FormatSubnetwork(args.subnetwork, project, location),
        endpointIp=args.endpoint_ip,
        description=args.description,
        labels=labels,
    )

    create_request = messages.DnsOutboundEndpointsCreateRequest(
        parent=parent,
        outboundEndpointId=endpoint_id,
        outboundEndpoint=outbound_endpoint,
    )

    operation = client.outboundEndpoints.Create(create_request)
    if args.async_:
      log.CreatedResource(
          endpoint_ref.RelativeName(),
          kind='OutboundEndpoint',
          is_async=True,
          details=f'with operation [{operation.name}]',
      )
      return operation

    operation_ref = util.GetRegistry(api_version).ParseRelativeName(
        operation.name, collection='dns.operations'
    )
    poller = waiter.CloudOperationPoller(
        client.outboundEndpoints, client.operations
    )
    response = waiter.WaitFor(
        poller,
        operation_ref,
        f'Creating OutboundEndpoint [{endpoint_ref.RelativeName()}]',
    )
    log.CreatedResource(endpoint_ref.RelativeName(), kind='OutboundEndpoint')
    return response
