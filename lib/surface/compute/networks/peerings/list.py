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
"""Command for listing network peerings."""

from googlecloudsdk.api_lib.compute import base_classes

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(base_classes.GlobalLister):
  """List Google Compute Engine network peerings."""

  @property
  def service(self):
    return self.compute.networks

  @property
  def resource_type(self):
    return 'peerings'

  @staticmethod
  def Args(parser):
    base_classes.GlobalLister.Args(parser)

    parser.add_argument(
        '--network',
        help='Only show peerings of a specific network.')

  def ComputeDynamicProperties(self, args, items):
    for network in items:
      for peering in network['peerings']:
        # Add network information to peering for output table
        peering['source_network'] = network['selfLink']
        yield peering

  def GetResources(self, args, errors):
    networks = super(ListAlpha, self).GetResources(args, errors)
    return (network for network in networks if network.peerings and args.network
            is None or network.name == args.network)

ListAlpha.detailed_help = base_classes.GetGlobalListerHelp('peerings')
