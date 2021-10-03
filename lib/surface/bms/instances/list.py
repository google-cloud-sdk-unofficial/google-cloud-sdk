# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""'Bare Metal Solution instances list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List Bare Metal Solution instances in a project.
        """,
    'EXAMPLES':
        """
          To list private clouds in the region within the project ``us-central1'', run:

            $ {command} --region=us-central1

          Or:

          To list all instances in the project, run:

            $ {command}
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Bare Metal Solution instances in a project."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    # Remove unsupported default List flags.
    base.FILTER_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

    flags.AddRegionArgToParser(parser)
    # The default format picks out the components of the relative name:
    # given projects/myproject/locations/us-central1/clusterGroups/my-test
    # it takes -1 (my-test), -3 (us-central1), and -5 (myproject).
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,name.segment(-5):label=PROJECT,'
        'name.segment(-3):label=REGION,machineType,'
        'clientNetworks[].ipAddress.notnull().list():label=CLIENT_IPS,'
        'privateNetworks[].ipAddress.notnull().list():label=PRIVATE_IPS,'
        'state)')

  def Run(self, args):
    region = args.CONCEPTS.region.Parse()
    client = BmsClient()
    if region is None:
      project = properties.VALUES.core.project.Get(required=True)
      for instance in client.AggregateList(project, limit=args.limit):
        synthesized_instance = self.synthesizedInstance(instance, client)
        yield synthesized_instance
    else:
      for instance in client.List(region, limit=args.limit):
        synthesized_instance = self.synthesizedInstance(instance, client)
        yield synthesized_instance

  def synthesizedInstance(self, instance, client):
    """Returns a synthesized Instance resource.

    Synthesized Instance has additional lists of networks for client and
    private.

    Args:
      instance: protorpc.messages.Message, The BMS instance.
      client: BmsClient, BMS API client.

    Returns:
      Synthesized Instance resource.

    """
    synthesized_instance = resource_projector.MakeSerializable(instance)
    client_networks = []
    private_networks = []
    for network in instance.networks:
      if client.IsClientNetwork(network):
        client_networks.append(network)
      elif client.IsPrivateNetwork(network):
        private_networks.append(network)
    synthesized_instance['clientNetworks'] = client_networks
    synthesized_instance['privateNetworks'] = private_networks
    return synthesized_instance


List.detailed_help = DETAILED_HELP
