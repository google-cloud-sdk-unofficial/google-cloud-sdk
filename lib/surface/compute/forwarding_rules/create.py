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
"""Command for creating forwarding rules."""

from googlecloudsdk.api_lib.compute import forwarding_rules_utils as utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags
from googlecloudsdk.core import log


def _Args(parser, include_beta, include_alpha=False):
  """Argument parsing."""
  flags.AddUpdateArgs(parser, include_beta=include_beta)
  flags.AddAddress(parser)
  flags.AddIPProtocols(parser, include_alpha=include_alpha)
  flags.AddDescription(parser)
  flags.AddPortsAndPortRange(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(utils.ForwardingRulesTargetMutator):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  FORWARDING_RULE_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    _Args(parser, include_beta=False, include_alpha=False)
    cls.FORWARDING_RULE_ARG.AddArgument(parser)

  @property
  def method(self):
    return 'Insert'

  def ConstructProtocol(self, args):
    if args.ip_protocol:
      return self.messages.ForwardingRule.IPProtocolValueValuesEnum(
          args.ip_protocol)
    else:
      return

  def CreateRequests(self, args):
    """Overrides."""
    self.global_request = getattr(args, 'global')

    if self.global_request:
      return self.CreateGlobalRequests(args)
    else:
      return self.CreateRegionalRequests(args)

  def CreateGlobalRequests(self, args):
    """Create a globally scoped request."""
    port_range = _ResolvePortRange(args.port_range, args.ports)
    if not port_range:
      raise exceptions.ToolException(
          '[--ports] is required for global forwarding rules.')
    target_ref = self.GetGlobalTarget(args)
    forwarding_rule_ref = self.FORWARDING_RULE_ARG.ResolveAsResource(
        args, self.resources)
    protocol = self.ConstructProtocol(args)

    request = self.messages.ComputeGlobalForwardingRulesInsertRequest(
        forwardingRule=self.messages.ForwardingRule(
            description=args.description,
            name=forwarding_rule_ref.Name(),
            IPAddress=args.address,
            IPProtocol=protocol,
            portRange=port_range,
            target=target_ref.SelfLink(),),
        project=self.project)

    return [request]

  def CreateRegionalRequests(self, args):
    """Create a regionally scoped request."""
    target_ref, region_ref = self.GetRegionalTarget(args)
    if not args.region and region_ref:
      args.region = region_ref
    forwarding_rule_ref = self.FORWARDING_RULE_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))
    protocol = self.ConstructProtocol(args)

    request = self.messages.ComputeForwardingRulesInsertRequest(
        forwardingRule=self.messages.ForwardingRule(
            description=args.description,
            name=forwarding_rule_ref.Name(),
            IPAddress=args.address,
            IPProtocol=protocol,
            portRange=_ResolvePortRange(args.port_range, args.ports),
            target=target_ref.SelfLink(),),
        project=self.project,
        region=forwarding_rule_ref.region)

    return [request]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    _Args(parser, include_beta=True, include_alpha=False)
    cls.FORWARDING_RULE_ARG.AddArgument(parser)

  def CreateRegionalRequests(self, args):
    """Create a regionally scoped request."""
    target_ref, region_ref = self.GetRegionalTarget(args)
    if not args.region and region_ref:
      args.region = region_ref
    forwarding_rule_ref = self.FORWARDING_RULE_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))
    protocol = self.ConstructProtocol(args)

    forwarding_rule = self.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=args.address,
        IPProtocol=protocol,
        portRange=args.port_range)
    if target_ref.Collection() == 'compute.regionBackendServices':
      forwarding_rule.loadBalancingScheme = (
          self.messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum(
              args.load_balancing_scheme))
      forwarding_rule.backendService = target_ref.SelfLink()
      if args.load_balancing_scheme == 'INTERNAL':
        if args.ports:
          forwarding_rule.portRange = None
          forwarding_rule.ports = [str(p) for p in _GetPortList(args.ports)]
        if args.subnet is not None:
          if not args.subnet_region:
            args.subnet_region = forwarding_rule_ref.region
          forwarding_rule.subnetwork = flags.SUBNET_ARG.ResolveAsResource(
              args, self.resources).SelfLink()
        if args.network is not None:
          forwarding_rule.network = flags.NETWORK_ARG.ResolveAsResource(
              args, self.resources).SelfLink()
    else:
      forwarding_rule.target = target_ref.SelfLink()
    request = self.messages.ComputeForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule,
        project=self.project,
        region=forwarding_rule_ref.region)

    return [request]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    _Args(parser, include_beta=True, include_alpha=True)
    cls.FORWARDING_RULE_ARG.AddArgument(parser)


Create.detailed_help = {
    'DESCRIPTION': ("""\
        *{{command}}* is used to create a forwarding rule. {overview}

        When creating a forwarding rule, exactly one of  ``--target-instance'',
        ``--target-pool'', ``--target-http-proxy'', ``--target-https-proxy'',
        ``--target-ssl-proxy'', or ``--target-vpn-gateway'' must be specified.
        """.format(overview=flags.FORWARDING_RULES_OVERVIEW)),
}

CreateBeta.detailed_help = Create.detailed_help
CreateAlpha.detailed_help = Create.detailed_help


def _GetPortRange(ports_range_list):
  """Return single range by combining the ranges."""
  if not ports_range_list:
    return None, None
  ports = sorted(ports_range_list)
  combined_port_range = ports.pop(0)
  for port_range in ports_range_list:
    try:
      combined_port_range = combined_port_range.Combine(port_range)
    except arg_parsers.Error:
      raise exceptions.InvalidArgumentException(
          '--ports', 'Must specify consecutive ports at this time.')
  return combined_port_range


def _ResolvePortRange(port_range, port_range_list):
  """Reconciles deprecated port_range value and list of port ranges."""
  if port_range:
    log.warn('The --port-range flag is deprecated. Use equivalent --ports=%s'
             ' flag.', port_range)
  elif port_range_list:
    port_range = _GetPortRange(port_range_list)
  return str(port_range) if port_range else None


def _GetPortList(range_list):
  ports = []
  for port_range in range_list:
    ports.extend(range(port_range.start, port_range.end + 1))
  return sorted(ports)
