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

"""Command for deleting transports."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete a transport.

  Delete the specified transport.
  """

  @staticmethod
  def Args(parser):
    flags.AddTransportResourceArg(parser, 'to delete')
    flags.AddAsyncFlag(parser)
    flags.AddRegionFlag(
        parser, supports_region_wildcard=True, hidden=False, required=True
    )

  def Run(self, args):
    client = networkconnectivity_api.TransportsClient(
        release_track=self.ReleaseTrack()
    )
    transport_ref = args.CONCEPTS.transport.Parse()

    console_io.PromptContinue(
        message=(
            'You are about to delete transport [{}]'.format(
                transport_ref.Name()
            )
        ),
        cancel_on_no=True,
    )

    op_ref = client.DeleteBeta(transport_ref)

    log.status.Print(
        'Delete request issued for: [{}]'.format(transport_ref.Name())
    )

    if op_ref.done:
      log.DeletedResource(transport_ref.Name(), kind='transport')
      return op_ref

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    api_version = networkconnectivity_util.VERSION_MAP[self.ReleaseTrack()]
    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='networkconnectivity.projects.locations.operations',
        api_version=api_version,
    )
    poller = waiter.CloudOperationPollerNoResources(client.operation_service)
    res = waiter.WaitFor(
        poller,
        op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name),
    )
    log.DeletedResource(transport_ref.Name(), kind='transport')
    return res


Delete.detailed_help = {
    'EXAMPLES': """ \
  To delete a transport named ``mytransport'' in the ``us-central1'' region, run:

    $ {command} mytransport --region=us-central1
  """,
    'API REFERENCE': """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
