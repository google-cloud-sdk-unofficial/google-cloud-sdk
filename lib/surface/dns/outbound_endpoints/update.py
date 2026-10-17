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
"""gcloud dns outbound-endpoints update command."""

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.dns import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  r"""Updates an existing Cloud DNS outbound endpoint.

  This command updates the description or labels of an existing Cloud DNS
  outbound endpoint.

  ## EXAMPLES

  To update the description of an outbound endpoint `my-endpoint` in `us-east1`,
  run:

    $ {command} my-endpoint --location=us-east1 \
        --description="Updated description"
  """

  @staticmethod
  def Args(parser):
    resource_args.AddOutboundEndpointResourceArg(
        parser, verb='to update', api_version='v1'
    )
    flags.GetOutboundEndpointDescriptionArg(required=False).AddToParser(parser)
    labels_util.AddUpdateLabelsFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat('json')

  def Run(self, args):
    api_version = 'v1'
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    endpoint_ref = args.CONCEPTS.outbound_endpoint.Parse()
    endpoint_name = endpoint_ref.RelativeName()

    get_request = messages.DnsOutboundEndpointsGetRequest(name=endpoint_name)
    to_update = client.outboundEndpoints.Get(get_request)

    update_mask = []
    if args.IsSpecified('description'):
      to_update.description = args.description
      update_mask.append('description')

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      labels_update = labels_diff.Apply(
          messages.OutboundEndpoint.LabelsValue, to_update.labels
      )
      if labels_update.needs_update:
        to_update.labels = labels_update.labels
        update_mask.append('labels')

    if not update_mask:
      log.status.Print('Nothing to update.')
      return to_update

    patch_request = messages.DnsOutboundEndpointsPatchRequest(
        name=endpoint_name,
        outboundEndpoint=to_update,
        updateMask=','.join(update_mask),
    )

    operation = client.outboundEndpoints.Patch(patch_request)
    if args.async_:
      log.UpdatedResource(
          endpoint_name,
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
        f'Updating OutboundEndpoint [{endpoint_name}]',
    )
    log.UpdatedResource(endpoint_name, kind='OutboundEndpoint')
    return response
