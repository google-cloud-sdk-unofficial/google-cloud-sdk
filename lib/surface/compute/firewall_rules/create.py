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
"""Command for creating firewall rules."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewalls_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.firewall_rules import flags
from googlecloudsdk.command_lib.compute.networks import flags as network_flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base_classes.BaseAsyncCreator):
  """Create a Google Compute Engine firewall rule.

  *{command}* is used to create firewall rules to allow incoming
  traffic to a network.
  """

  FIREWALL_RULE_ARG = None
  NETWORK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_RULE_ARG = flags.FirewallRuleArgument()
    cls.FIREWALL_RULE_ARG.AddArgument(parser)
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        'The network to which this rule is attached.', required=False)
    firewalls_utils.AddCommonArgs(parser, for_update=False)

  @property
  def service(self):
    return self.compute.firewalls

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'firewalls'

  def _CreateFirewall(self, args):
    allowed = firewalls_utils.ParseRules(args.allow, self.messages,
                                         firewalls_utils.ActionType.ALLOW)

    network_ref = self.NETWORK_ARG.ResolveAsResource(args, self.resources)
    firewall_ref = self.FIREWALL_RULE_ARG.ResolveAsResource(args,
                                                            self.resources)
    if not args.source_ranges and not args.source_tags:
      args.source_ranges = ['0.0.0.0/0']

    return self.messages.Firewall(
        allowed=allowed,
        name=firewall_ref.Name(),
        description=args.description,
        network=network_ref.SelfLink(),
        sourceRanges=args.source_ranges,
        sourceTags=args.source_tags,
        targetTags=args.target_tags)

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding firewall rules."""
    firewall = self._CreateFirewall(args)
    request = self.messages.ComputeFirewallsInsertRequest(
        firewall=firewall, project=self.project)
    return [request]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaCreate(Create):
  """Create a Google Compute Engine firewall rule.

  *{command}* is used to create firewall rules to allow/deny
  incoming/outgoing traffic.
  """

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_RULE_ARG = flags.FirewallRuleArgument()
    cls.FIREWALL_RULE_ARG.AddArgument(parser)
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        'The network to which this rule is attached.', required=False)
    firewalls_utils.AddCommonArgs(
        parser, for_update=False, with_egress_support=True)

  def Collection(self):
    """Returns the resource collection path."""
    return 'compute.firewalls.alpha'

  def _CreateFirewall(self, args):
    if args.rules and args.allow:
      raise firewalls_utils.ArgumentValidationError(
          'Can NOT specify --rules and --allow in the same request.')

    if bool(args.action) ^ bool(args.rules):
      raise firewalls_utils.ArgumentValidationError(
          'Must specify --rules with --action.')

    allowed = firewalls_utils.ParseRules(args.allow, self.messages,
                                         firewalls_utils.ActionType.ALLOW)

    network_ref = self.NETWORK_ARG.ResolveAsResource(args, self.resources)
    firewall_ref = self.FIREWALL_RULE_ARG.ResolveAsResource(
        args, self.resources)

    firewall = self.messages.Firewall(
        allowed=allowed,
        name=firewall_ref.Name(),
        description=args.description,
        network=network_ref.SelfLink(),
        sourceRanges=args.source_ranges,
        sourceTags=args.source_tags,
        targetTags=args.target_tags)

    firewall.direction = None
    if args.direction and args.direction in ['EGRESS', 'OUT']:
      firewall.direction = (
          self.messages.Firewall.DirectionValueValuesEnum.EGRESS)
    else:
      firewall.direction = (
          self.messages.Firewall.DirectionValueValuesEnum.INGRESS)

    firewall.priority = args.priority
    firewall.destinationRanges = args.destination_ranges

    allowed = []
    denied = []
    if not args.action:
      allowed = firewalls_utils.ParseRules(
          args.allow, self.messages, firewalls_utils.ActionType.ALLOW)
    elif args.action == 'ALLOW':
      allowed = firewalls_utils.ParseRules(
          args.rules, self.messages, firewalls_utils.ActionType.ALLOW)
    elif args.action == 'DENY':
      denied = firewalls_utils.ParseRules(
          args.rules, self.messages, firewalls_utils.ActionType.DENY)
    firewall.allowed = allowed
    firewall.denied = denied
    return firewall


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaCreate(BetaCreate):
  """Create a Google Compute Engine firewall rule.

  *{command}* is used to create firewall rules to allow/deny
  incoming/outgoing traffic.
  """

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_RULE_ARG = flags.FirewallRuleArgument()
    cls.FIREWALL_RULE_ARG.AddArgument(parser)
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        'The network to which this rule is attached.', required=False)
    firewalls_utils.AddCommonArgs(
        parser,
        for_update=False,
        with_egress_support=True,
        with_service_account=True)
    firewalls_utils.AddArgsForServiceAccount(parser, for_update=False)

  def Collection(self):
    """Returns the resource collection path."""
    return 'compute.firewalls.alpha'

  def _CreateFirewall(self, args):
    firewall = super(AlphaCreate, self)._CreateFirewall(args)
    firewall.sourceServiceAccounts = args.source_service_accounts
    firewall.targetServiceAccounts = args.target_service_accounts
    return firewall
