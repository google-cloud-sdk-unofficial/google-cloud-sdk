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


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
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

    network = parser.add_argument(
        '--network',
        default='default',
        help='The network to which this rule is attached.')
    network.detailed_help = """\
        The network to which this rule is attached. If omitted, the
        rule is attached to the ``default'' network.
        """

  @property
  def service(self):
    return self.compute.firewalls

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'firewalls'

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding firewall rules."""
    if not args.source_ranges and not args.source_tags:
      args.source_ranges = ['0.0.0.0/0']

    allowed = firewalls_utils.ParseRules(args.allow, self.messages,
                                         firewalls_utils.ActionType.ALLOW)

    network_ref = self.NETWORK_ARG.ResolveAsResource(args, self.resources)
    firewall_ref = self.FIREWALL_RULE_ARG.ResolveAsResource(args,
                                                            self.resources)

    request = self.messages.ComputeFirewallsInsertRequest(
        firewall=self.messages.Firewall(
            allowed=allowed,
            name=firewall_ref.Name(),
            description=args.description,
            network=network_ref.SelfLink(),
            sourceRanges=args.source_ranges,
            sourceTags=args.source_tags,
            targetTags=args.target_tags),
        project=self.project)
    return [request]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaCreate(Create):
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

    network = parser.add_argument(
        '--network',
        default='default',
        help='The network to which this rule is attached.')
    network.detailed_help = """\
        The network to which this rule is attached. If omitted, the
        rule is attached to the ``default'' network.
        """

  def Collection(self):
    """Returns the resource collection path."""
    return 'compute.firewalls.alpha'

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding firewall rules."""

    # TODO(user): remove the check once allow was deprecated.
    if args.rules and args.allow:
      raise firewalls_utils.ArgumentValidationError(
          'Can NOT specify --rules and --allow in the same request.')

    if bool(args.action) ^ bool(args.rules):
      raise firewalls_utils.ArgumentValidationError(
          'Must specify --rules with --action.')

    direction = None
    if args.direction and args.direction in ['EGRESS', 'OUT']:
      direction = self.messages.Firewall.DirectionValueValuesEnum.EGRESS
    else:
      direction = self.messages.Firewall.DirectionValueValuesEnum.INGRESS

    priority = args.priority

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

    network_ref = self.CreateGlobalReference(
        args.network, resource_type='networks')
    firewall_ref = self.CreateGlobalReference(
        args.name, resource_type='firewalls')

    request = self.messages.ComputeFirewallsInsertRequest(
        firewall=self.messages.Firewall(
            allowed=allowed,
            denied=denied,
            direction=direction,
            priority=priority,
            name=firewall_ref.Name(),
            description=args.description,
            network=network_ref.SelfLink(),
            sourceRanges=args.source_ranges,
            destinationRanges=args.destination_ranges,
            sourceTags=args.source_tags,
            targetTags=args.target_tags),
        project=self.project)
    return [request]
