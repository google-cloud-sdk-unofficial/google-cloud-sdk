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

"""Command for creating subnetworks."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.command_lib.compute.networks.subnets import flags


class Create(base_classes.BaseAsyncCreator):
  """Define a subnet for a network in custom subnet mode."""

  NETWORK_ARG = None
  SUBNETWORK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SUBNETWORK_ARG = flags.SubnetworkArgument()
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        'The network to which the subnetwork belongs.')
    cls.SUBNETWORK_ARG.AddArgument(parser)
    cls.NETWORK_ARG.AddArgument(parser)

    parser.add_argument(
        '--description',
        help='An optional description of this subnetwork.')

    parser.add_argument(
        '--range',
        required=True,
        help='The IP space allocated to this subnetwork in CIDR format.')

  @property
  def service(self):
    return self.compute.subnetworks

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'subnetworks'

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding a subnetwork."""

    network_ref = self.NETWORK_ARG.ResolveAsResource(args, self.resources)
    subnet_ref = self.SUBNETWORK_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))

    request = self.messages.ComputeSubnetworksInsertRequest(
        subnetwork=self.messages.Subnetwork(
            name=subnet_ref.Name(),
            description=args.description,
            network=network_ref.SelfLink(),
            ipCidrRange=args.range
        ),
        region=subnet_ref.region,
        project=self.project)

    return [request]
