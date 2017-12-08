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

"""Command for updating an interface on a router."""

import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.command_lib.compute.vpn_tunnels import (flags as
                                                            vpn_tunnel_flags)
from googlecloudsdk.core import exceptions


class InterfaceNotFoundError(exceptions.Error):
  """Raised when an interface is not found."""

  def __init__(self, name):
    self.name = name
    msg = 'interface `{0}` not found'.format(name)
    super(InterfaceNotFoundError, self
         ).__init__(msg)


class RequireMaskError(exceptions.Error):
  """Raised when a mask is needed but not provided."""

  def __init__(self):
    super(RequireMaskError, self).__init__(
        '--ip-address', '--mask-length must be set if --ip-address is set')


class UpdateInterface(base_classes.ReadWriteCommand):
  """Update an interface on a router."""

  ROUTER_ARG = None
  VPN_TUNNEL_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='update')
    cls.VPN_TUNNEL_ARG = vpn_tunnel_flags.VpnTunnelArgumentForRouter(
        required=False, operation_type='updated')
    cls.VPN_TUNNEL_ARG.AddArgument(parser)

    parser.add_argument(
        '--interface-name',
        required=True,
        help='The name of the interface being updated.')

    parser.add_argument(
        '--ip-address',
        type=utils.IPV4Argument,
        help='The link local address of the router for this interface.')

    parser.add_argument(
        '--mask-length',
        type=int,
        # TODO(b/36051080): better help
        help='The mask for network used for the server IP address.')

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

    iface = None
    for i in replacement.interfaces:
      if i.name == args.interface_name:
        iface = i
        break

    if iface is None:
      raise InterfaceNotFoundError(args.interface_name)

    if args.mask_length is not None:
      if args.mask_length < 0 or args.mask_length > 31:
        raise exceptions.Error(
            '--mask-length must be a non-negative integer less than 32')

    if args.ip_address is not None:
      if args.mask_length is None:
        raise RequireMaskError()

      iface.ipRange = '{0}/{1}'.format(args.ip_address, args.mask_length)

    if not args.vpn_tunnel_region:
      args.vpn_tunnel_region = replacement.region

    if args.vpn_tunnel is not None:
      vpn_ref = self.VPN_TUNNEL_ARG.ResolveAsResource(
          args,
          self.resources,
          scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client))
      iface.linkedVpnTunnel = vpn_ref.SelfLink()

    return replacement


UpdateInterface.detailed_help = {
    'DESCRIPTION': """
        *{command}* is used to update an interface on a router.
        """,
}
