# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command for creating network firewall policy packet mirrorig rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewall_policy_rule_utils as rule_utils
from googlecloudsdk.api_lib.compute.network_firewall_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags
from googlecloudsdk.command_lib.compute.network_firewall_policies import secure_tags_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  r"""Creates a Compute Engine network firewall policy packet mirroring rule.

  *{command}* is used to create network firewall policy packet mirroring rules.
  """

  NETWORK_FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_FIREWALL_POLICY_ARG = (
        flags.NetworkFirewallPolicyPacketMirroringRuleArgument(
            required=True, operation='create'
        )
    )
    cls.NETWORK_FIREWALL_POLICY_ARG.AddArgument(parser, operation_type='create')
    flags.AddPacketMirroringAction(parser)
    flags.AddRulePriority(parser, operation='inserted')
    flags.AddSrcIpRanges(parser)
    flags.AddDestIpRanges(parser)
    flags.AddLayer4Configs(parser)
    flags.AddDirection(parser)
    flags.AddDisabled(parser)
    flags.AddTargetServiceAccounts(parser)
    flags.AddDescription(parser)
    flags.AddGlobalFirewallPolicy(parser)
    flags.AddSrcSecureTags(parser)
    flags.AddTargetSecureTags(parser)
    flags.AddSrcAddressGroups(parser)
    flags.AddDestAddressGroups(parser)
    flags.AddSrcFqdns(parser)
    flags.AddDestFqdns(parser)
    flags.AddSrcRegionCodes(parser)
    flags.AddDestRegionCodes(parser)
    flags.AddSrcThreatIntelligence(parser)
    flags.AddDestThreatIntelligence(parser)
    flags.AddSecurityProfileGroup(parser)

    parser.display_info.AddCacheUpdater(flags.NetworkFirewallPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.NETWORK_FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources
    )
    network_firewall_policy_rule_client = (
        client.NetworkFirewallPolicyPacketMirroringRule(
            ref=ref, compute_client=holder.client
        )
    )

    src_ip_ranges = []
    dest_ip_ranges = []
    layer4_configs = []
    target_service_accounts = []
    security_profile_group = None
    disabled = False
    src_secure_tags = []
    target_secure_tags = []
    if args.IsSpecified('src_ip_ranges'):
      src_ip_ranges = args.src_ip_ranges
    if args.IsSpecified('dest_ip_ranges'):
      dest_ip_ranges = args.dest_ip_ranges
    if args.IsSpecified('layer4_configs'):
      layer4_configs = args.layer4_configs
    if args.IsSpecified('target_service_accounts'):
      target_service_accounts = args.target_service_accounts
    if args.IsSpecified('disabled'):
      disabled = args.disabled
    if args.IsSpecified('src_secure_tags'):
      src_secure_tags = secure_tags_utils.TranslateSecureTagsForFirewallPolicy(
          holder.client, args.src_secure_tags
      )
    if args.IsSpecified('target_secure_tags'):
      target_secure_tags = (
          secure_tags_utils.TranslateSecureTagsForFirewallPolicy(
              holder.client, args.target_secure_tags
          )
      )
    if args.IsSpecified('security_profile_group'):
      security_profile_group = args.security_profile_group

    layer4_config_list = rule_utils.ParseLayer4Configs(
        layer4_configs, holder.client.messages
    )
    matcher = holder.client.messages.FirewallPolicyRuleMatcher(
        srcIpRanges=src_ip_ranges,
        destIpRanges=dest_ip_ranges,
        layer4Configs=layer4_config_list,
        srcSecureTags=src_secure_tags,
    )
    if args.IsSpecified('src_address_groups'):
      matcher.srcAddressGroups = args.src_address_groups
    if args.IsSpecified('dest_address_groups'):
      matcher.destAddressGroups = args.dest_address_groups
    if args.IsSpecified('src_fqdns'):
      matcher.srcFqdns = args.src_fqdns
    if args.IsSpecified('dest_fqdns'):
      matcher.destFqdns = args.dest_fqdns
    if args.IsSpecified('src_region_codes'):
      matcher.srcRegionCodes = args.src_region_codes
    if args.IsSpecified('dest_region_codes'):
      matcher.destRegionCodes = args.dest_region_codes
    if args.IsSpecified('src_threat_intelligence'):
      matcher.srcThreatIntelligences = args.src_threat_intelligence
    if args.IsSpecified('dest_threat_intelligence'):
      matcher.destThreatIntelligences = args.dest_threat_intelligence
    traffic_direct = (
        holder.client.messages.FirewallPolicyRule.DirectionValueValuesEnum.INGRESS
    )
    if args.IsSpecified('direction'):
      if args.direction == 'INGRESS':
        traffic_direct = (
            holder.client.messages.FirewallPolicyRule.DirectionValueValuesEnum.INGRESS
        )
      else:
        traffic_direct = (
            holder.client.messages.FirewallPolicyRule.DirectionValueValuesEnum.EGRESS
        )

    firewall_policy_rule = holder.client.messages.FirewallPolicyRule(
        priority=rule_utils.ConvertPriorityToInt(args.priority),
        action=args.action,
        match=matcher,
        direction=traffic_direct,
        targetServiceAccounts=target_service_accounts,
        description=args.description,
        disabled=disabled,
        targetSecureTags=target_secure_tags,
        securityProfileGroup=security_profile_group,
    )

    return network_firewall_policy_rule_client.CreateRule(
        firewall_policy=args.firewall_policy,
        firewall_policy_rule=firewall_policy_rule,
    )


Create.detailed_help = {
    'EXAMPLES': """\
    To create a rule with priority ``10'' in a global network firewall policy
    with name ``my-policy'' and description ``example rule'', run:

        $ {command} 10 --firewall-policy=my-policy --action=do_not_mirror --description="example rule" --global-firewall-policy
    """,
}
