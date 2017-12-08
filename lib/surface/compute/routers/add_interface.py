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

"""Command for adding an interface to a router."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.third_party.py27 import py27_copy as copy


class AddInterface(base_classes.ReadWriteCommand):
  """Add an interface to a router."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--interface-name',
        required=True,
        help='The name of the interface being added.')

    parser.add_argument(
        '--vpn-tunnel',
        required=True,
        help='The tunnel of the interface being added.')

    parser.add_argument(
        '--ip-address',
        type=utils.IPV4Argument,
        help='The link local address of the router for this interface.')

    parser.add_argument(
        '--mask-length',
        type=int,
        # TODO(user): better help
        help='The mask for network used for the server IP address.')

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

    mask = None

    interface_name = args.interface_name

    if args.mask_length is not None:
      if args.mask_length < 0 or args.mask_length > 31:
        raise exceptions.ToolException(
            '--mask-length must be a non-negative integer less than 32')

    if args.ip_address is not None:
      if args.mask_length is not None:
        mask = '{0}/{1}'.format(args.ip_address, args.mask_length)
      else:
        raise exceptions.ToolException(
            '--ip-address', '--mask-length must be set if --ip-address is set')

    vpn_ref = self.CreateRegionalReference(
        args.vpn_tunnel, args.region, resource_type='vpnTunnels')

    interface = self.messages.RouterInterface(
        name=interface_name,
        linkedVpnTunnel=vpn_ref.SelfLink(),
        ipRange=mask)

    replacement.interfaces.append(interface)

    return replacement


AddInterface.detailed_help = {
    'DESCRIPTION': """
        *{command}* is used to add an interface to a router.
        """,
}
