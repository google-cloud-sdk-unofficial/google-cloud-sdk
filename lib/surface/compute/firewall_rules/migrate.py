# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command for migrate from legacy firewall rules to network firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _GetFirewallPoliciesAssociatedWithNetwork(network, firewall_policies):
  filtered_policies = []
  for firewall_policy in firewall_policies:
    associated = False
    for association in firewall_policy.associations:
      if association.attachmentTarget == network.selfLink:
        associated = True
    if associated:
      filtered_policies.append(firewall_policy)
  return filtered_policies


def _GetFirewallsAssociatedWithNetwork(network, firewalls):
  filtered_firewalls = []
  for firewall in firewalls:
    if firewall.network == network.selfLink:
      filtered_firewalls.append(firewall)
  return filtered_firewalls


def _IsDefaultFirewallPolicyRule(rule):
  # Default egress/ingress IPv4/IPv6 rules
  if 2147483644 <= rule.priority <= 2147483647:
    return True
  # Probably a user defined rule
  return False


def _IsFirewallSupported(firewall):
  """Checks if the given VPC Firewall can be converted by the Migration Tool."""
  # Source Service Accounts
  if firewall.sourceServiceAccounts:
    return (False, 'Firewalls with source_service_accounts are not supported.')
  # Source Tags
  if firewall.sourceTags:
    return (False, 'Firewalls with source_tags are not supported.')
  # Target Tags
  if firewall.targetTags:
    return (False, 'Firewalls with target_tags are not supported.')
  # Logging is not supported in Network Firewall Policies MVP
  if firewall.logConfig and firewall.logConfig.enable:
    return (False, 'Logging is not supported in Network Firewall Policy MVP.')
  return (True, '')


def _IsGkeFirewall(firewall):
  return re.match(r'gke-(.*)-(.*)', firewall.name)


def _IsCustomerDefinedFirewall(firewall):
  return not _IsGkeFirewall(firewall)


def _ConvertRuleDirection(messages, direction):
  if direction == messages.Firewall.DirectionValueValuesEnum.INGRESS:
    return messages.FirewallPolicyRule.DirectionValueValuesEnum.INGRESS
  return messages.FirewallPolicyRule.DirectionValueValuesEnum.EGRESS


def _ConvertRuleInternal(messages, firewall, action, l4_configs):
  layer4_configs = []
  for config in l4_configs:
    layer4_configs.append(
        messages.FirewallPolicyRuleMatcherLayer4Config(
            ipProtocol=config.IPProtocol, ports=config.ports))

  return messages.FirewallPolicyRule(
      disabled=firewall.disabled,
      ruleName=firewall.name,  # Allow and deny cannot be in the same rule
      description=firewall.description,  # Do not change description
      direction=_ConvertRuleDirection(messages, firewall.direction),
      priority=firewall.priority,
      action=action,
      enableLogging=False,  # =firewall.logConfig.enable : is not supported yet
      match=messages.FirewallPolicyRuleMatcher(
          destIpRanges=firewall.destinationRanges,
          srcIpRanges=firewall.sourceRanges,
          layer4Configs=layer4_configs),
      targetServiceAccounts=firewall.targetServiceAccounts)


def _ConvertRule(messages, firewall):
  if firewall.denied:
    return _ConvertRuleInternal(messages, firewall, 'deny', firewall.denied)
  return _ConvertRuleInternal(messages, firewall, 'allow', firewall.allowed)


def _IsPrefixTrue(statuses):
  false_detected = False
  for status in statuses:
    if status and false_detected:
      return False
    false_detected = false_detected or not status
  return True


def _IsSuffixTrue(statuses):
  statuses_copy = statuses
  statuses_copy.reverse()
  return _IsPrefixTrue(statuses_copy)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class MigrateAlpha(base.CreateCommand):
  """Migrate from legacy firewall rules to network firewall policies."""

  NETWORK_ARG = None
  FIREWALL_POLICY_ARG_NAME = 'FIREWALL_POLICY'

  @classmethod
  def Args(cls, parser):
    # positional FIREWALL_POLICY argument
    parser.add_argument(
        cls.FIREWALL_POLICY_ARG_NAME,
        help="""\
      Name of the new Network Firewall Policy used to store the migration
      result.
      """)
    # positional required --network=NETWORK flag
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        'The VPC Network for which the migration should be performed.',
        required=True)
    cls.NETWORK_ARG.AddArgument(parser)

  def Run(self, args):
    """Run the migration logic."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE

    # Determine project
    if args.project:
      project = args.project
    else:
      project = properties.VALUES.core.project.GetOrFail()

    # Get Input Parameters
    network_name = getattr(args, 'network')
    policy_name = getattr(args, self.FIREWALL_POLICY_ARG_NAME)

    # Get VPC Network
    network = client.networks.Get(
        messages.ComputeNetworksGetRequest(
            project=project, network=network_name))

    log.status.Print(
        'Looking for VPC Firewalls and Network Firewall Policies associated with VPC Network \'{}\'.'
        .format(network_name))

    # Get all Firewall Policies
    response = client.networkFirewallPolicies.List(
        messages.ComputeNetworkFirewallPoliciesListRequest(project=project))

    # Verify there is no Firewall Policy with provided name
    for firewall_policy in response.items:
      if firewall_policy.name == policy_name:
        log.status.Print('Firewall Policy "' + policy_name +
                         '" already exists.')
        return

    # Filter Network Firewall Policies attached to the given VPC Network
    firewall_policies = _GetFirewallPoliciesAssociatedWithNetwork(
        network, response.items)
    log.status.Print(
        'Found {} Network Firewall Policies associated with the VPC Network \'{}\'.'
        .format(len(firewall_policies), network_name))

    # Migration tool does not support multiple FirewallPolicies.
    if len(firewall_policies) > 1:
      log.status.Print(
          'Migration tool does not support multiple Network Firewall Policies '
          'associated with a single VPC Network.')
      return

    # List all legacy VPC Firewalls attached to the given VPC Network
    # Hidden VPC Firewalls are not listed.
    # TODO(b/222646415) Support more than 500 VPC Firewalls (maxResults)!
    response = client.firewalls.List(
        messages.ComputeFirewallsListRequest(project=project))
    firewalls = _GetFirewallsAssociatedWithNetwork(network, response.items)
    log.status.Print(
        'Found {} VPC Firewalls associated with the VPC Network \'{}\'.\n'
        .format(len(firewalls), network_name))

    # Sort VPC Firewalls by priorities. If two Firewalls have the same priority
    # then deny rules should precede allow rules. Third coordinate is unique to
    # avoid comparison between Firewall objects which is undefined.

    # Add unique ID to each firewall
    firewalls_temp = []
    firewalls_counter = 0
    for firewall in firewalls:
      firewalls_temp.append((firewalls_counter, firewall))
      firewalls_counter = firewalls_counter + 1
    # Build tuple
    firewalls = [
        (f.priority, 0 if f.denied else 1, id, f) for (id, f) in firewalls_temp
    ]
    firewalls = sorted(firewalls)

    # Convert user provided VPC Firewalls if possible
    converted_firewalls = []
    conversion_failures = 0
    customer_defined_firewalls = 0
    for (priority, _, _, firewall) in firewalls:
      (status, error) = (False, 'Not a customer defined VPC Firewall.')
      converted_firewall = None
      is_custom = _IsCustomerDefinedFirewall(firewall)
      # Convert only supported customer defined VPC Firewalls
      if is_custom:
        customer_defined_firewalls = customer_defined_firewalls + 1
        (status, error) = _IsFirewallSupported(firewall)
        if status:
          converted_firewall = _ConvertRule(messages, firewall)
        else:
          conversion_failures = conversion_failures + 1
      converted_firewalls.append(
          (priority, firewall, is_custom, converted_firewall, status, error))

    # Print info about detected customer defined VPC Firewalls.
    log.status.Print('Found {} customer defined VPC Firewalls.'.format(
        customer_defined_firewalls))
    log.status.Print('priority: name \'description\'')
    for (_, firewall, is_custom, _, _, _) in converted_firewalls:
      if is_custom:
        log.status.Print('{}: {} \'{}\''.format(firewall.priority,
                                                firewall.name,
                                                firewall.description))
    log.status.Print('')

    # Print info about conversion failures
    if conversion_failures:
      log.status.Print(
          'Could not convert {} VPC Firewalls:'.format(conversion_failures))
      for (_, firewall, _, _, status, error) in converted_firewalls:
        if not status:
          log.status.Print('{}: {} - {}'.format(firewall.priority,
                                                firewall.name, error))
      log.status.Print('')

    # Filter out default FirewallPolicy.Rules
    # There is at most one firewall policy to iterate on.
    firewall_policy_rules = []
    for firewall_policy in firewall_policies:
      for rule in firewall_policy.rules:
        if not _IsDefaultFirewallPolicyRule(rule):
          firewall_policy_rules.append(rule)

    # Sort FirewallPolicy.Rules by priority
    firewall_policy_rules = [
        (rule.priority, rule) for rule in firewall_policy_rules
    ]
    firewall_policy_rules = sorted(firewall_policy_rules)

    # Adjust the format to match list of converted VPC Firewalls
    firewall_policy_rules = [(priority, None, True, rule, True, '')
                             for (priority, rule) in firewall_policy_rules]

    # Join converted VPC Firewalls with Network Firewall Policy Rules
    joined_rules = []
    if network.networkFirewallPolicyEnforcementOrder == messages.Network.NetworkFirewallPolicyEnforcementOrderValueValuesEnum.AFTER_CLASSIC_FIREWALL:
      joined_rules.extend(converted_firewalls)
      joined_rules.extend(firewall_policy_rules)
    else:
      joined_rules.extend(firewall_policy_rules)
      joined_rules.extend(converted_firewalls)

    # Check if extraction of selected rules is possible
    # Extracted rules must be a prefix for BEFORE_CLASSIC_FIREWALL mode and
    # suffix for AFTER_CLASSIC_FIREWALL mode.
    statuses = [status for (_, _, _, _, status, _) in joined_rules]
    if network.networkFirewallPolicyEnforcementOrder == messages.Network.NetworkFirewallPolicyEnforcementOrderValueValuesEnum.AFTER_CLASSIC_FIREWALL:
      if not _IsSuffixTrue(statuses):
        log.status.Print(
            'Migration is impossible, because rule evaluation order cannot be preserved.'
        )
        return
    else:
      if not _IsPrefixTrue(statuses):
        log.status.Print(
            'Migration is impossible, because rule evaluation order cannot be preserved.'
        )
        return

    # Extract rules to migrate
    rules_to_migrate = [(p, r, f) for (p, f, _, r, s, _) in joined_rules if s]

    # Check if priorities remap is needed
    priorities_remap_needed = (
        len(set([p for (p, r, f) in rules_to_migrate])) !=
        len(rules_to_migrate))

    # Compute new priorities if needed
    if priorities_remap_needed:
      log.status.Print('Updating rules priorities to avoid collisions.')
      log.status.Print(
          'new-priority: old-priority rule-name \'rule-description\'')

    current_priority = 1000
    migrated_rules = []
    for (priority, rule, firewall) in rules_to_migrate:
      if priorities_remap_needed:
        rule.priority = current_priority
        current_priority = current_priority + 1
        log.status.Print('{}: {} {} \'{}\''.format(rule.priority, priority,
                                                   rule.ruleName,
                                                   rule.description))
      migrated_rules.append((rule, firewall))
    if priorities_remap_needed:
      log.status.Print('')

    # Create a new Network Firewall Policy
    firewall_policy = messages.FirewallPolicy(
        description='Network Firewall Policy containing all VPC Firewalls and FirewallPolicy.Rules migrated using GCP Firewall Migration Tool.',
        name=policy_name,
        vpcNetworkScope=messages.FirewallPolicy.VpcNetworkScopeValueValuesEnum
        .GLOBAL_VPC_NETWORK)
    response = client.networkFirewallPolicies.Insert(
        messages.ComputeNetworkFirewallPoliciesInsertRequest(
            project=project, firewallPolicy=firewall_policy))
    # Wait until Network Firewall Policy is created
    operation_poller = poller.Poller(client.networkFirewallPolicies)
    operation_ref = holder.resources.Parse(
        response.selfLink, collection='compute.globalOperations')
    waiter.WaitFor(
        operation_poller, operation_ref,
        'Creating new Network Firewall Policy \'{}\''.format(policy_name))

    # Add migrated rules to newly created policy
    log.status.Print('Successfully migrated the following VPC Firewalls:')
    log.status.Print('old-priority: rule-name \'rule-description\'')
    for (rule, firewall) in migrated_rules:
      client.networkFirewallPolicies.AddRule(
          messages.ComputeNetworkFirewallPoliciesAddRuleRequest(
              firewallPolicy=policy_name,
              firewallPolicyRule=rule,
              project=project))
      if firewall:
        log.status.Print('{}: {} \'{}\''.format(firewall.priority,
                                                firewall.name,
                                                firewall.description))


MigrateAlpha.detailed_help = {
    'brief':
        'Create a new Network Firewall Policy and move all customer defined '
        'firewall rules there.',
    'DESCRIPTION':
        """
*{command}* is used to create a new Network Firewall Policy that contain
all rules defined in already existing Network Firewall Policy associated with
the given VPC Network and all customer defined VPC Firewall Rules attached to
that VPC Network.
""",
    'EXAMPLES':
        """
To execute the migration for VPC Network 'my-network' which stores the result
in 'my-policy' Network Firewall Policy, run:

  $ {command} my-policy --network=my-network
  """,
}
