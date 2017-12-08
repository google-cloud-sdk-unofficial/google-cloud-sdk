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

"""Command for creating routers."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags


class Create(base_classes.BaseAsyncCreator):
  """Define a router."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--description',
        help='An optional description of this router.')

    parser.add_argument(
        '--network',
        required=True,
        help='The network for this router')

    parser.add_argument(
        '--asn',
        required=True,
        type=int,
        # TODO(user): improve this help
        help='The BGP asn for this router')

    flags.AddRegionFlag(
        parser,
        resource_type='router',
        operation_type='create')

    parser.add_argument(
        'name',
        help='The name of the router.')

  @property
  def service(self):
    return self.compute.routers

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'routers'

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding a router."""
    router_ref = self.CreateRegionalReference(args.name, args.region)
    network_ref = self.CreateGlobalReference(
        args.network, resource_type='networks')

    request = self.messages.ComputeRoutersInsertRequest(
        router=self.messages.Router(
            description=args.description,
            network=network_ref.SelfLink(),
            bgp=self.messages.RouterBgp(
                asn=args.asn),
            name=router_ref.Name()),
        region=router_ref.region,
        project=self.project)

    return [request]

Create.detailed_help = {
    'brief': 'Create a router',
    'DESCRIPTION': """
        *{command}* is used to create a router for use in dynamic
        routing with vpn tunnels.
     """
    }
