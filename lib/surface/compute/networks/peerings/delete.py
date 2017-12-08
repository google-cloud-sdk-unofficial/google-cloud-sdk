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
"""Command for deleting network peerings."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import networks_utils
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(base_classes.BaseAsyncMutator):
  """Delete a Google Compute Engine network peering."""

  @property
  def service(self):
    return self.compute.networks

  @property
  def method(self):
    return 'RemovePeering'

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
        help='The name of the peering to delete.')

    parser.add_argument(
        '--network',
        required=True,
        help='The name of the network in the current project containing the '
             'peering.')

  def CreateRequests(self, args):
    """Returns the request necessary for deleting the peering."""

    request = self.messages.ComputeNetworksRemovePeeringRequest(
        network=args.network,
        networksRemovePeeringRequest=self.messages.NetworksRemovePeeringRequest(
            name=args.name),
        project=self.project)

    return [request]
