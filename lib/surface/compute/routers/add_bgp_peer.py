# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Command for adding a BGP peer to a router."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.third_party.py27 import py27_copy as copy


class AddBgpPeer(base_classes.ReadWriteCommand):
  """Add a BGP peer to a router."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--peer-name',
        required=True,
        help='The name of the peer being added.')

    parser.add_argument(
        '--interface',
        required=True,
        help='The interface of the peer being added.')

    parser.add_argument(
        '--peer-asn',
        required=True,
        type=int,
        help='The asn of the peer being added.')

    parser.add_argument(
        '--peer-ip-address',
        help='The link local address of the peer.')

    parser.add_argument(
        # TODO(user): document the default priority if any
        '--advertised-route-priority',
        type=int,
        help='The priority of routes advertised to this BGP peer. In the case '
             'where there is more than one matching route of maximum length, '
             'the routes with lowest priority value win. 0 <= priority <= '
             '65535.')

    flags.AddRegionFlag(
        parser,
        resource_type='router',
        operation_type='update')

    parser.add_argument(
        'name',
        help='The name of the router.')

  @property
  def service(self):
    return self.compute.routers

  @property
  def resource_type(self):
    return 'routers'

  def CreateReference(self, args):
    return self.CreateRegionalReference(args.name, args.region)

  def GetGetRequest(self, args):
    return (self.service,
            'Get',
            self.messages.ComputeRoutersGetRequest(
                router=self.ref.Name(),
                region=self.ref.region,
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    return (self.service,
            'Update',
            self.messages.ComputeRoutersUpdateRequest(
                router=self.ref.Name(),
                routerResource=replacement,
                region=self.ref.region,
                project=self.project))

  def Modify(self, args, existing):
    replacement = copy.deepcopy(existing)

    peer = self.messages.RouterBgpPeer(
        name=args.peer_name,
        interfaceName=args.interface,
        peerIpAddress=args.peer_ip_address,
        peerAsn=args.peer_asn,
        advertisedRoutePriority=args.advertised_route_priority)

    replacement.bgpPeers.append(peer)

    return replacement


AddBgpPeer.detailed_help = {
    'DESCRIPTION': """
        *{command}* is used to add a BGP peer to a router.
        """,
}
