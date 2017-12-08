# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Command for creating target VPN Gateways."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags


class Create(base_classes.BaseAsyncCreator):
  """Create a VPN Gateway."""

  # Placeholder to indicate that a detailed_help field exists and should
  # be set outside the class definition.
  detailed_help = None

  @staticmethod
  def Args(parser):
    """Adds arguments to the supplied parser."""

    parser.add_argument(
        '--description',
        help='An optional, textual description for the target VPN Gateway.')

    network = parser.add_argument(
        '--network',
        required=True,
        help='A reference to a network in this project')
    network.detailed_help = """\
       A reference to a network in this project to
       contain the VPN Gateway.
       """

    flags.AddRegionFlag(
        parser,
        resource_type='Target VPN Gatway',
        operation_type='create')

    parser.add_argument(
        'name',
        help='The name of the target VPN Gateway.')

  @property
  def service(self):
    return self.compute.targetVpnGateways

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'targetVpnGateways'

  def CreateRequests(self, args):
    """Builds API requests to construct Target VPN Gateways.

    Args:
      args: argparse.Namespace, The arguments received by this command.

    Returns:
      [protorpc.messages.Message], A list of requests to be executed
      by the compute API.
    """

    target_vpn_gateway_ref = self.CreateRegionalReference(
        args.name, args.region, resource_type='targetVpnGateways')
    network_ref = self.CreateGlobalReference(
        args.network, resource_type='networks')
    # Get a reference to the region name in the gateway. N.B. This could have
    # been passed as part of args.region or resolved via a prompt.
    region_ref = self.CreateGlobalReference(
        target_vpn_gateway_ref.region, resource_type='regions')

    request = self.messages.ComputeTargetVpnGatewaysInsertRequest(
        project=self.project,
        region=region_ref.Name(),
        targetVpnGateway=self.messages.TargetVpnGateway(
            description=args.description,
            name=target_vpn_gateway_ref.Name(),
            network=network_ref.SelfLink()
            ))
    return [request]

Create.detailed_help = {
    'brief': 'Create a target VPN Gateway',
    'DESCRIPTION': """
        *{command}* is used to create a target VPN Gateway. A target VPN
        Gateway can reference one or more VPN tunnels that connect it to
        external VPN gateways. A VPN Gateway may also be referenced by
        one or more forwarding rules that define which packets the
        gateway is responsible for routing.
        """
    }
