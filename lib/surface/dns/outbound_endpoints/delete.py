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
"""gcloud dns outbound-endpoints delete command."""

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  r"""Deletes a Cloud DNS outbound endpoint.

  This command deletes a Cloud DNS outbound endpoint in a specified region.

  ## EXAMPLES

  To delete an outbound endpoint `my-endpoint` in `us-east1`, run:

    $ {command} my-endpoint --location=us-east1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddOutboundEndpointResourceArg(
        parser, verb='to delete', api_version='v1'
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    api_version = 'v1'
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    endpoint_ref = args.CONCEPTS.outbound_endpoint.Parse()
    endpoint_name = endpoint_ref.RelativeName()

    if not console_io.PromptContinue(
        message=f'You are about to delete outbound endpoint [{endpoint_name}]',
        throw_if_unattended=True,
    ):
      log.status.Print('Aborted by user.')
      return None

    request = messages.DnsOutboundEndpointsDeleteRequest(name=endpoint_name)
    operation = client.outboundEndpoints.Delete(request)
    if args.async_:
      log.DeletedResource(
          endpoint_name,
          kind='OutboundEndpoint',
          is_async=True,
          details=f'with operation [{operation.name}]',
      )
      return operation

    operation_ref = util.GetRegistry(api_version).ParseRelativeName(
        operation.name, collection='dns.operations'
    )
    poller = waiter.CloudOperationPollerNoResources(client.operations)
    response = waiter.WaitFor(
        poller,
        operation_ref,
        f'Deleting OutboundEndpoint [{endpoint_name}]',
    )
    log.DeletedResource(endpoint_name, kind='OutboundEndpoint')
    return response
