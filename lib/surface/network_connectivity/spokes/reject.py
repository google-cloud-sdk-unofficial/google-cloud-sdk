# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Command for accepting spokes."""

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


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Reject(base.Command):
  """Reject a spoke.

  Reject a VPC spoke. By rejecting a spoke,
  you prevent or remove connectivity between the associated VPC network
  and any other VPC networks that are attached to the same hub.
  """

  @staticmethod
  def Args(parser):
    flags.AddSpokeResourceArg(parser, 'to reject', vpc_spoke_only_command=True)
    flags.AddRegionGroup(parser, hide_region_arg=True)
    flags.AddRejectionDetailsFlag(parser)
    flags.AddAsyncFlag(parser)

  def Run(self, args):
    client = networkconnectivity_api.SpokesClient(
        release_track=self.ReleaseTrack())
    spoke_ref = args.CONCEPTS.spoke.Parse()
    op_ref = client.Reject(spoke_ref, args.details)

    log.status.Print('Reject request issued for: [{}]'.format(
        spoke_ref.Name()))

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='networkconnectivity.projects.locations.operations',
        api_version=networkconnectivity_util.VERSION_MAP[self.ReleaseTrack()])
    poller = waiter.CloudOperationPoller(client.spoke_service,
                                         client.operation_service)

    if op_ref.done:
      return poller.GetResult(op_resource)

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='networkconnectivity.projects.locations.operations',
        api_version=networkconnectivity_util.VERSION_MAP[self.ReleaseTrack()])
    poller = waiter.CloudOperationPoller(client.spoke_service,
                                         client.operation_service)
    res = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))
    return res


Reject.detailed_help = {
    'EXAMPLES':
        """ \
  To reject a spoke named ``myspoke'' with reason ``myreason'', run:

    $ {command} myspoke --details="myreason" --global
  """,
    'API REFERENCE':
        """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
