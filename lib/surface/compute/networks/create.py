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
"""Command for creating networks."""

import textwrap

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import networks_utils
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.networks import flags
from googlecloudsdk.core import log


class Create(base_classes.BaseAsyncCreator):
  """Create a Google Compute Engine network.

  *{command}* is used to create virtual networks. A network
  performs the same function that a router does in a home
  network: it describes the network range and gateway IP
  address, handles communication between instances, and serves
  as a gateway between instances and callers outside the
  network.
  """

  NETWORK_ARG = None

  @property
  def service(self):
    return self.compute.networks

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'networks'

  def ComputeDynamicProperties(self, args, items):
    self._network_name = args.name
    return networks_utils.AddMode(items)

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_ARG = flags.NetworkArgument()
    cls.NETWORK_ARG.AddArgument(parser)

    parser.add_argument(
        '--description',
        help='An optional, textual description for the network.')

    parser.add_argument(
        '--mode',
        metavar='NETWORK_TYPE',
        choices={
            'auto': (
                'Subnets are created automatically. This is the recommended '
                'selection.'),
            'custom': 'Create subnets manually.',
            'legacy': (
                'Create an old style network that has a range and cannot have '
                'subnets.'),
        },
        required=False,
        help='The network type.')
    range_arg = parser.add_argument(
        '--range',
        help='Specifies the IPv4 address range of this network.')
    range_arg.detailed_help = """\
        Specifies the IPv4 address range of legacy mode networks. The range
        must be specified in CIDR format:
        [](http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing)

        This flag only works if mode is legacy.
        """

  def CreateRequests(self, args):
    """Returns the request necessary for adding the network."""

    # TODO(b/31649473): after one month, make default auto.
    if args.mode is None:
      if args.range is not None:
        log.warn('You are creating a legacy network. Using --mode=legacy will '
                 'be required in future releases.')
        args.mode = 'legacy'
      else:
        args.mode = 'auto'

    if args.mode != 'legacy' and args.range is not None:
      raise exceptions.InvalidArgumentException(
          '--range', '--range can only be used if --mode=legacy')

    network_ref = self.NETWORK_ARG.ResolveAsResource(args, self.resources)

    if args.mode == 'legacy':
      return [self.messages.ComputeNetworksInsertRequest(
          network=self.messages.Network(
              name=network_ref.Name(),
              IPv4Range=args.range,
              description=args.description),
          project=self.project)]

    request = self.messages.ComputeNetworksInsertRequest(
        network=self.messages.Network(
            name=network_ref.Name(),
            autoCreateSubnetworks=args.mode == 'auto',
            description=args.description),
        project=self.project)

    return [request]

  def Epilog(self, resources_were_displayed=True):
    message = """\

        Instances on this network will not be reachable until firewall rules
        are created. As an example, you can allow all internal traffic between
        instances as well as SSH, RDP, and ICMP by running:

        $ gcloud compute firewall-rules create <FIREWALL_NAME> --network {0} --allow tcp,udp,icmp --source-ranges <IP_RANGE>
        $ gcloud compute firewall-rules create <FIREWALL_NAME> --network {0} --allow tcp:22,tcp:3389,icmp
        """.format(self._network_name)
    log.status.Print(textwrap.dedent(message))
