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
"""Command for modifying the target of forwarding rules."""

from googlecloudsdk.api_lib.compute import forwarding_rules_utils as utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Set(utils.ForwardingRulesTargetMutator):
  """Modify a forwarding rule to direct network traffic to a new target."""

  FORWARDING_RULE_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    flags.AddUpdateArgs(parser, include_beta=False)
    cls.FORWARDING_RULE_ARG.AddArgument(parser)

  @property
  def method(self):
    return 'SetTarget'

  def CreateRequests(self, args):
    """Overrides."""
    forwarding_rule_ref = self.FORWARDING_RULE_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))

    self.global_request = getattr(forwarding_rule_ref, 'region', None) is None
    if self.global_request:
      return self.CreateGlobalRequests(forwarding_rule_ref, args)
    else:
      return self.CreateRegionalRequests(forwarding_rule_ref, args)

  def CreateGlobalRequests(self, forwarding_rule_ref, args):
    """Create a globally scoped request."""
    target_ref = self.GetGlobalTarget(args)

    request = self.messages.ComputeGlobalForwardingRulesSetTargetRequest(
        forwardingRule=forwarding_rule_ref.Name(),
        project=self.project,
        targetReference=self.messages.TargetReference(
            target=target_ref.SelfLink(),
        ),
    )

    return [request]

  def CreateRegionalRequests(self, forwarding_rule_ref, args):
    """Create a regionally scoped request."""
    target_ref, _ = self.GetRegionalTarget(
        args, forwarding_rule_ref=forwarding_rule_ref)

    request = self.messages.ComputeForwardingRulesSetTargetRequest(
        forwardingRule=forwarding_rule_ref.Name(),
        project=self.project,
        region=forwarding_rule_ref.region,
        targetReference=self.messages.TargetReference(
            target=target_ref.SelfLink(),
        ),
    )

    return [request]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SetBeta(Set):
  """Modify a forwarding rule to direct network traffic to a new target."""

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    flags.AddUpdateArgs(parser, include_beta=True)
    cls.FORWARDING_RULE_ARG.AddArgument(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetAlpha(Set):
  """Modify a forwarding rule to direct network traffic to a new target."""

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    flags.AddUpdateArgs(parser, include_beta=True, include_alpha=True)
    cls.FORWARDING_RULE_ARG.AddArgument(parser)


Set.detailed_help = {
    'brief': ('Modify a forwarding rule to direct network traffic to a new '
              'target'),
    'DESCRIPTION': ("""\
        *{{command}}* is used to set a new target for a forwarding
        rule. {overview}

        When creating a forwarding rule, exactly one of  ``--target-instance'',
        ``--target-pool'', ``--target-http-proxy'', ``--target-https-proxy'',
        ``--target-ssl-proxy'', or ``--target-vpn-gateway'' must be specified.
        """.format(overview=flags.FORWARDING_RULES_OVERVIEW)),
}

SetBeta.detailed_help = Set.detailed_help

SetAlpha.detailed_help = {
    'brief': ('Modify a forwarding rule to direct network traffic to a new '
              'target'),
    'DESCRIPTION': ("""\
        *{{command}}* is used to set a new target for a forwarding
        rule. {overview}

        When creating a forwarding rule, exactly one of  ``--target-instance'',
        ``--target-pool'', ``--target-http-proxy'', ``--target-https-proxy'',
        ``--target-ssl-proxy'', ``--target-tcp-proxy'' or
        ``--target-vpn-gateway'' must be specified.""".format(
            overview=flags.FORWARDING_RULES_OVERVIEW)),
}
