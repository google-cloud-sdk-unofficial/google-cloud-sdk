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
"""Command for updating firewall rules."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewalls_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.firewall_rules import flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class UpdateFirewall(base_classes.ReadWriteCommand):
  """Update a firewall rule."""
  with_egress_firewall = False

  FIREWALL_RULE_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_RULE_ARG = flags.FirewallRuleArgument(operation_type='update')
    cls.FIREWALL_RULE_ARG.AddArgument(parser)
    firewalls_utils.AddCommonArgs(parser, for_update=True)

  @property
  def service(self):
    return self.compute.firewalls

  @property
  def resource_type(self):
    return 'firewalls'

  def CreateReference(self, args):
    return self.FIREWALL_RULE_ARG.ResolveAsResource(args, self.resources)

  def Run(self, args):
    self.new_allowed = firewalls_utils.ParseRules(
        args.allow, self.messages, firewalls_utils.ActionType.ALLOW)

    args_unset = (args.allow is None
                  and args.description is None
                  and args.source_ranges is None
                  and args.source_tags is None
                  and args.target_tags is None)
    if self.with_egress_firewall:
      args_unset = (args_unset and args.destination_ranges is None and
                    args.priority is None and args.rules is None)
    if args_unset:
      raise calliope_exceptions.ToolException(
          'At least one property must be modified.')

    return super(UpdateFirewall, self).Run(args)

  def GetGetRequest(self, args):
    """Returns the request for the existing Firewall resource."""
    return (self.service,
            'Get',
            self.messages.ComputeFirewallsGetRequest(
                firewall=self.ref.Name(),
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    return (self.service,
            'Update',
            self.messages.ComputeFirewallsUpdateRequest(
                firewall=replacement.name,
                firewallResource=replacement,
                project=self.project))

  def Modify(self, args, existing):
    """Returns a modified Firewall message."""
    if args.allow is None:
      allowed = existing.allowed
    else:
      allowed = self.new_allowed

    if args.description:
      description = args.description
    elif args.description is None:
      description = existing.description
    else:
      description = None

    if args.source_ranges:
      source_ranges = args.source_ranges
    elif args.source_ranges is None:
      source_ranges = existing.sourceRanges
    else:
      source_ranges = []

    if args.source_tags:
      source_tags = args.source_tags
    elif args.source_tags is None:
      source_tags = existing.sourceTags
    else:
      source_tags = []

    if args.target_tags:
      target_tags = args.target_tags
    elif args.target_tags is None:
      target_tags = existing.targetTags
    else:
      target_tags = []

    new_firewall = self.messages.Firewall(
        name=existing.name,
        allowed=allowed,
        description=description,
        network=existing.network,
        sourceRanges=source_ranges,
        sourceTags=source_tags,
        targetTags=target_tags,
    )

    return new_firewall


UpdateFirewall.detailed_help = {
    'brief': 'Update a firewall rule',
    'DESCRIPTION': """\
        *{command}* is used to update firewall rules that allow incoming
        traffic to a network. Only arguments passed in will be updated on the
        firewall rule.  Other attributes will remain unaffected.
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaUpdateFirewall(UpdateFirewall):
  """Update a firewall rule."""
  with_egress_firewall = True

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_RULE_ARG = flags.FirewallRuleArgument(operation_type='update')
    cls.FIREWALL_RULE_ARG.AddArgument(parser)
    firewalls_utils.AddCommonArgs(parser, True, True)

  def Modify(self, args, existing):
    """Returns a modified Firewall message."""

    # TODO(user): Remove the check once allow was deprecated.
    if args.rules and args.allow:
      raise firewalls_utils.ArgumentValidationError(
          'Can NOT specify --rules and --allow in the same request.')

    new_firewall = super(AlphaUpdateFirewall, self).Modify(args, existing)

    if args.rules:
      if existing.allowed:
        new_firewall.allowed = firewalls_utils.ParseRules(
            args.rules, self.messages, firewalls_utils.ActionType.ALLOW)
      else:
        new_firewall.denied = firewalls_utils.ParseRules(
            args.rules, self.messages, firewalls_utils.ActionType.DENY)

    new_firewall.direction = existing.direction

    if args.priority is None:
      new_firewall.priority = existing.priority
    else:
      new_firewall.priority = args.priority

    if args.destination_ranges is None:
      new_firewall.destinationRanges = existing.destinationRanges
    else:
      new_firewall.destinationRanges = args.destination_ranges

    return new_firewall


AlphaUpdateFirewall.detailed_help = {
    'brief': 'Update a firewall rule',
    'DESCRIPTION': """\
        *{command}* is used to update firewall rules that allow/deny
        incoming/outgoing traffic. Only arguments passed in will be updated on
        the firewall rule.  Other attributes will remain unaffected.
        """,
}
