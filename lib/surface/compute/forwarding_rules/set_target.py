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
from googlecloudsdk.command_lib.compute.forwarding_rules import flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Set(utils.ForwardingRulesTargetMutator):
  """Modify a forwarding rule to direct network traffic to a new target."""

  @staticmethod
  def Args(parser):
    flags.AddCommonFlags(parser)
    flags.AddUpdateArgs(parser,
                        include_alpha_targets=False,
                        include_beta_targets=False)

  @property
  def method(self):
    return 'SetTarget'

  def CreateGlobalRequests(self, args):
    """Create a globally scoped request."""

    forwarding_rule_ref = self.CreateGlobalReference(
        args.name, resource_type='globalForwardingRules')
    target_ref = self.GetGlobalTarget(args)

    request = self.messages.ComputeGlobalForwardingRulesSetTargetRequest(
        forwardingRule=forwarding_rule_ref.Name(),
        project=self.project,
        targetReference=self.messages.TargetReference(
            target=target_ref.SelfLink(),
        ),
    )

    return [request]

  def CreateRegionalRequests(self, args):
    """Create a regionally scoped request."""

    forwarding_rule_ref = self.CreateRegionalReference(
        args.name, args.region, flag_names=['--region', '--global'])
    target_ref, _ = self.GetRegionalTarget(args, forwarding_rule_ref)

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

  @staticmethod
  def Args(parser):
    flags.AddCommonFlags(parser)
    flags.AddUpdateArgs(parser,
                        include_alpha_targets=False,
                        include_beta_targets=True)

  def GetGlobalTarget(self, args):
    if args.target_ssl_proxy:
      return self.CreateGlobalReference(
          args.target_ssl_proxy, resource_type='targetSslProxies')
    return super(SetBeta, self).GetGlobalTarget(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetAlpha(SetBeta):
  """Modify a forwarding rule to direct network traffic to a new target."""

  @staticmethod
  def Args(parser):
    flags.AddCommonFlags(parser)
    flags.AddUpdateArgs(parser,
                        include_alpha_targets=True,
                        include_beta_targets=True)


Set.detailed_help = {
    'brief': ('Modify a forwarding rule to direct network traffic to a new '
              'target'),
    'DESCRIPTION': ("""\
        *{{command}}* is used to set a new target for a forwarding
        rule. {overview}

        When creating a forwarding rule, exactly one of  ``--target-instance'',
        ``--target-pool'', ``--target-http-proxy'', ``--target-https-proxy'',
        or ``--target-vpn-gateway'' must be specified.
        """.format(overview=flags.FORWARDING_RULES_OVERVIEW)),
}

SetBeta.detailed_help = {
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

SetAlpha.detailed_help = SetBeta.detailed_help
