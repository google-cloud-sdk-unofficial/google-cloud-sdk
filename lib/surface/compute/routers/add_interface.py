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
"""Command for adding an interface to a Google Compute Engine router."""

import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import routers_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.interconnects.attachments import (
    flags as attachment_flags)
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.command_lib.compute.vpn_tunnels import (flags as
                                                            vpn_tunnel_flags)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class AddInterface(base_classes.ReadWriteCommand):
  """Add an interface to a Google Compute Engine router."""

  ROUTER_ARG = None
  VPN_TUNNEL_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='update')
    cls.VPN_TUNNEL_ARG = vpn_tunnel_flags.VpnTunnelArgumentForRouter()
    cls.VPN_TUNNEL_ARG.AddArgument(parser)

    routers_utils.AddCommonArgs(parser)

  @property
  def service(self):
    return self.compute.routers

  @property
  def resource_type(self):
    return 'routers'

  def CreateReference(self, args):
    return self.ROUTER_ARG.ResolveAsResource(args, self.resources)

  def GetGetRequest(self, args):
    return (self.service, 'Get', self.messages.ComputeRoutersGetRequest(
        router=self.ref.Name(), region=self.ref.region, project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    return (self.service, 'Update', self.messages.ComputeRoutersUpdateRequest(
        router=self.ref.Name(),
        routerResource=replacement,
        region=self.ref.region,
        project=self.project))

  def Modify(self, args, existing):
    replacement = copy.deepcopy(existing)

    mask = None

    interface_name = args.interface_name

    if args.mask_length is not None:
      if args.mask_length < 0 or args.mask_length > 31:
        raise parser_errors.ArgumentException(
            '--mask-length must be a non-negative integer less than 32')

    if args.ip_address is not None:
      if args.mask_length is not None:
        mask = '{0}/{1}'.format(args.ip_address, args.mask_length)
      else:
        raise parser_errors.ArgumentException(
            '--mask-length must be set if --ip-address is set')

    if not args.vpn_tunnel_region:
      args.vpn_tunnel_region = replacement.region
    vpn_ref = self.VPN_TUNNEL_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client))

    interface = self.messages.RouterInterface(
        name=interface_name, linkedVpnTunnel=vpn_ref.SelfLink(), ipRange=mask)

    replacement.interfaces.append(interface)

    return replacement


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaAddInterface(AddInterface):
  """Add an interface to a Google Compute Engine router."""

  ROUTER_ARG = None
  VPN_TUNNEL_ARG = None
  INTERCONNECT_ATTACHMENT_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='update')

    link_parser = parser.add_mutually_exclusive_group(
        required=True)

    cls.VPN_TUNNEL_ARG = vpn_tunnel_flags.VpnTunnelArgumentForRouter(
        required=False)
    cls.VPN_TUNNEL_ARG.AddArgument(link_parser)

    cls.INTERCONNECT_ATTACHMENT_ARG = (
        attachment_flags.InterconnectAttachmentArgumentForRouter())
    cls.INTERCONNECT_ATTACHMENT_ARG.AddArgument(link_parser)

    routers_utils.AddCommonArgs(parser)

  def Modify(self, args, existing):
    replacement = copy.deepcopy(existing)
    mask = None
    interface_name = args.interface_name

    if args.mask_length is not None:
      if args.mask_length < 0 or args.mask_length > 31:
        raise parser_errors.ArgumentException(
            '--mask-length must be a non-negative integer less than 32')

    if args.ip_address is not None:
      if args.mask_length is not None:
        mask = '{0}/{1}'.format(args.ip_address, args.mask_length)
      else:
        raise parser_errors.ArgumentException(
            '--mask-length must be set if --ip-address is set')

    if not args.vpn_tunnel_region:
      args.vpn_tunnel_region = replacement.region
    vpn_ref = None
    if args.vpn_tunnel is not None:
      vpn_ref = self.VPN_TUNNEL_ARG.ResolveAsResource(
          args,
          self.resources,
          scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client))

    if not args.interconnect_attachment_region:
      args.interconnect_attachment_region = replacement.region
    attachment_ref = None
    if args.interconnect_attachment is not None:
      attachment_ref = self.INTERCONNECT_ATTACHMENT_ARG.ResolveAsResource(
          args, self.resources)

    interface = self.messages.RouterInterface(
        name=interface_name,
        linkedVpnTunnel=(vpn_ref.SelfLink() if vpn_ref else None),
        linkedInterconnectAttachment=(attachment_ref.SelfLink()
                                      if attachment_ref else None),
        ipRange=mask)

    replacement.interfaces.append(interface)

    return replacement


AddInterface.detailed_help = {
    'DESCRIPTION':
        """
        *{command}* is used to add an interface to a Google Compute Engine
        router.
        """,
}
