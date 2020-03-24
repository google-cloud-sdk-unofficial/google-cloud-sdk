# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Command for getting effective firewalls of GCP networks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.networks import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class GetEffectiveFirewalls(base.Command):
  """Get the effective firewalls of a Google Compute Engine network.

  *{command}* Get the effective firewalls applied on the network. For example:

    $ {command} example-network

  gets the effective firewalls applied on the network 'example-network'.
  """

  @staticmethod
  def Args(parser):
    flags.NetworkArgument().AddArgument(
        parser, operation_type='get effective firewalls')

  def SortNetworkFirewallRules(self, client, rules):
    ingress_network_firewall = [
        item for item in rules if item.direction ==
        client.messages.Firewall.DirectionValueValuesEnum.INGRESS
    ]
    ingress_network_firewall.sort(key=lambda x: x.priority, reverse=False)
    egress_network_firewall = [
        item for item in rules if item.direction ==
        client.messages.Firewall.DirectionValueValuesEnum.EGRESS
    ]
    egress_network_firewall.sort(key=lambda x: x.priority, reverse=False)
    return ingress_network_firewall + egress_network_firewall

  def SortOrgFirewallRules(self, client, rules):
    ingress_org_firewall_rule = [
        item for item in rules if item.direction ==
        client.messages.SecurityPolicyRule.DirectionValueValuesEnum.INGRESS
    ]
    ingress_org_firewall_rule.sort(key=lambda x: x.priority, reverse=False)
    egress_org_firewall_rule = [
        item for item in rules if item.direction ==
        client.messages.SecurityPolicyRule.DirectionValueValuesEnum.EGRESS
    ]
    egress_org_firewall_rule.sort(key=lambda x: x.priority, reverse=False)
    return ingress_org_firewall_rule + egress_org_firewall_rule

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    network_ref = flags.NetworkArgument().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = client.messages.ComputeNetworksGetEffectiveFirewallsRequest(
        **network_ref.AsDict())
    responses = client.MakeRequests([(client.apitools_client.networks,
                                      'GetEffectiveFirewalls', request)])
    res = responses[0]
    org_firewall = []
    network_firewall = []
    if hasattr(res, 'firewalls'):
      network_firewall = self.SortNetworkFirewallRules(client, res.firewalls)

    if hasattr(res, 'organizationFirewalls'):
      for sp in res.organizationFirewalls:
        org_firewall_rule = self.SortOrgFirewallRules(client, sp.rules)
        org_firewall.append(
            client.messages
            .NetworksGetEffectiveFirewallsResponseOrganizationFirewallPolicy(
                id=sp.id, rules=org_firewall_rule))
    return client.messages.NetworksGetEffectiveFirewallsResponse(
        organizationFirewalls=org_firewall, firewalls=network_firewall)


GetEffectiveFirewalls.detailed_help = {
    'EXAMPLES':
        """\
    To get the effective firewalls of network with name example-network, run:

      $ {command} example-network,
    """,
}
