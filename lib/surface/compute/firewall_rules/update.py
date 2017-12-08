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
class UpdateFirewall(base_classes.BaseCommand):
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

  def Format(self, unused_args):
    # Do not print the modifed the firewall in the output.
    return 'none'

  def _CreateReference(self, args):
    return self.FIREWALL_RULE_ARG.ResolveAsResource(args, self.resources)

  def ValidateArgument(self, args):
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

  def Run(self, args):
    self.ValidateArgument(args)
    # Set the resource reference which used in composing resource-get request.
    resource_reference = self._CreateReference(args)
    get_request = self._GetGetRequest(resource_reference, args)
    cleared_fields = []
    objects = self.compute_client.MakeRequests([get_request])

    new_object = self.Modify(args, objects[0], cleared_fields)

    # If existing object is equal to the proposed object or if
    # Modify() returns None, then there is no work to be done, so we
    # print the resource and return.
    if not new_object or objects[0] == new_object:
      return objects[0]

    with self.compute.IncludeFields(cleared_fields):
      resource_list = self.compute_client.MakeRequests(
          [self._GetSetRequest(args, new_object, objects[0])])

    return resource_list

  def _GetGetRequest(self, resource_reference, args):
    """Returns the request for the existing Firewall resource."""
    return (self.service, 'Get', self.messages.ComputeFirewallsGetRequest(
        firewall=resource_reference.Name(), project=self.project))

  def _GetSetRequest(self, args, replacement, existing):
    request = (self.messages.ComputeFirewallsPatchRequest(
        firewall=replacement.name,
        firewallResource=replacement,
        project=self.project))
    return (self.service, 'Patch', request)

  def Modify(self, args, existing, cleared_fields):
    """Returns a modified Firewall message and included fields."""
    if args.allow is None:
      allowed = existing.allowed
    else:
      allowed = self.new_allowed

    if args.description:
      description = args.description
    elif args.description is None:
      description = existing.description
    else:
      cleared_fields.append('description')
      description = None

    if args.source_ranges:
      source_ranges = args.source_ranges
    elif args.source_ranges is None:
      source_ranges = existing.sourceRanges
    else:
      cleared_fields.append('sourceRanges')
      source_ranges = []

    if args.source_tags:
      source_tags = args.source_tags
    elif args.source_tags is None:
      source_tags = existing.sourceTags
    else:
      cleared_fields.append('sourceTags')
      source_tags = []

    if args.target_tags:
      target_tags = args.target_tags
    elif args.target_tags is None:
      target_tags = existing.targetTags
    else:
      cleared_fields.append('targetTags')
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

  def ValidateArgument(self, args):
    super(AlphaUpdateFirewall, self).ValidateArgument(args)
    if args.rules and args.allow:
      raise firewalls_utils.ArgumentValidationError(
          'Can NOT specify --rules and --allow in the same request.')

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_RULE_ARG = flags.FirewallRuleArgument(operation_type='update')
    cls.FIREWALL_RULE_ARG.AddArgument(parser)
    firewalls_utils.AddCommonArgs(parser, True, True)

  def Modify(self, args, existing, cleared_fields):
    """Returns a modified Firewall message."""

    # TODO(user): Remove the check once allow was deprecated.
    new_firewall = super(AlphaUpdateFirewall, self).Modify(
        args, existing, cleared_fields)

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

    if args.destination_ranges:
      new_firewall.destinationRanges = args.destination_ranges
    elif args.destination_ranges is None:
      new_firewall.destinationRanges = existing.destinationRanges
    else:
      new_firewall.destinationRanges = []
      cleared_fields.append('destinationRanges')

    return new_firewall


AlphaUpdateFirewall.detailed_help = {
    'brief': 'Update a firewall rule',
    'DESCRIPTION': """\
        *{command}* is used to update firewall rules that allow/deny
        incoming/outgoing traffic. Only arguments passed in will be updated on
        the firewall rule.  Other attributes will remain unaffected.
        """,
}
