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

"""Command for updating a BGP peer to a router."""

import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.core import exceptions


class PeerNotFoundError(exceptions.Error):
  """Raised when a peer is not found."""

  def __init__(self, name):
    self.name = name
    msg = 'peer `{0}` not found'.format(name)
    super(PeerNotFoundError, self
         ).__init__(msg)


class UpdateBgpPeer(base_classes.ReadWriteCommand):
  """Update a BGP peer on a router."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='update')

    parser.add_argument(
        '--peer-name',
        required=True,
        help='The name of the peer being modified.')

    parser.add_argument(
        '--interface',
        help='The new interface of the peer being modified.')

    parser.add_argument(
        '--peer-asn',
        type=int,
        help='The new asn of the peer being modified.')

    parser.add_argument(
        '--ip-address',
        help='The new link local address of the router for this peer.')

    parser.add_argument(
        '--peer-ip-address',
        help='The new link local address of the peer.')

    parser.add_argument(
        '--advertised-route-priority',
        type=int,
        help='The priority of routes advertised to this BGP peer. In the case '
             'where there is more than one matching route of maximum length, '
             'the routes with lowest priority value win. 0 <= priority <= '
             '65535.')

  @property
  def service(self):
    return self.compute.routers

  @property
  def resource_type(self):
    return 'routers'

  def CreateReference(self, args):
    return self.ROUTER_ARG.ResolveAsResource(args, self.resources)

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

    peer = None
    for p in replacement.bgpPeers:
      if p.name == args.peer_name:
        peer = p
        break

    if peer is None:
      raise PeerNotFoundError(args.peer_name)

    attrs = {
        'interfaceName': args.interface,
        'ipAddress': args.ip_address,
        'peerIpAddress': args.peer_ip_address,
        'peerAsn': args.peer_asn,
        'advertisedRoutePriority': args.advertised_route_priority,
    }

    for attr, value in attrs.items():
      if value is not None:
        setattr(peer, attr, value)

    return replacement


UpdateBgpPeer.detailed_help = {
    'DESCRIPTION': """
        *{command}* is used to update a BGP peer on a router.
        """,
}
