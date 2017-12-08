# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command for creating network peerings."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import networks_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base_classes.BaseAsyncMutator):
  """Create a Google Compute Engine network peering."""

  @property
  def service(self):
    return self.compute.networks

  @property
  def method(self):
    return 'AddPeering'

  @property
  def resource_type(self):
    return 'peerings'

  def ComputeDynamicProperties(self, args, items):
    self._network_name = args.name
    return networks_utils.AddMode(items)

  @staticmethod
  def Args(parser):

    parser.add_argument(
        'name',
        help='The name of the peering.')

    parser.add_argument(
        '--network',
        required=True,
        help='The name of the network in the current project to be peered '
             'with the peer network.')

    parser.add_argument(
        '--peer-network',
        required=True,
        help='The name of the network to be peered with the current network.')

    parser.add_argument(
        '--peer-project',
        required=False,
        help='The name of the project for the peer network.  If not specified, '
             'defaults to current project.')

    parser.add_argument(
        '--auto-create-routes',
        action='store_true',
        default=False,
        required=False,
        help='If set, will automatically create routes for the network '
             'peering.  Note that a backend error will be returned if this is '
             'not set.')

  def CreateRequests(self, args):
    """Returns the request necessary for adding the peering."""

    peer_network_ref = resources.REGISTRY.Parse(
        args.peer_network,
        params={'project': args.peer_project or self.project},
        collection='compute.networks')

    request = self.messages.ComputeNetworksAddPeeringRequest(
        network=args.network,
        networksAddPeeringRequest=self.messages.NetworksAddPeeringRequest(
            autoCreateRoutes=args.auto_create_routes,
            name=args.name,
            peerNetwork=peer_network_ref.RelativeName()),
        project=self.project)
    return [request]
