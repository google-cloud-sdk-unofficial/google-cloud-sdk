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
import ipaddr


def _Args(parser, include_beta, include_alpha=False):
  """Argument parsing."""
  flags.AddUpdateArgs(parser, include_beta=include_beta,
                      include_alpha=include_alpha)
  flags.AddIPProtocols(parser)
  flags.AddDescription(parser)
  flags.AddPortsAndPortRange(parser)
  flags.AddNetworkTier(parser, include_alpha=include_alpha)
  if include_alpha:
    parser.add_argument(
        '--service-label',
        help='(Only for Internal Load Balancing): '
             'https://cloud.google.com/compute/docs/load-balancing/internal/\n'
             'The DNS label to use as the prefix of the fully qualified domain '
             'name for this forwarding rule. The full name will be internally '
             'generated and output as dnsName. If this field is not specified, '
             'no DNS record will be generated and no DNS name will be output. ')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(utils.ForwardingRulesTargetMutator):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  FORWARDING_RULE_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    _Args(parser, include_beta=False, include_alpha=False)
    flags.ADDRESS_ARG.AddArgument(parser)
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
    forwarding_rule_ref = self.FORWARDING_RULE_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))

    if forwarding_rule_ref.Collection() == 'compute.globalForwardingRules':
      self.global_request = True
      return self._CreateGlobalRequests(args, forwarding_rule_ref)
    else:
      self.global_request = False
      return self._CreateRegionalRequests(args, forwarding_rule_ref)

  def _CreateGlobalRequests(self, args, forwarding_rule_ref):
    """Create a globally scoped request."""
    port_range = _ResolvePortRange(args.port_range, args.ports)
    if not port_range:
      raise exceptions.ToolException(
          '[--ports] is required for global forwarding rules.')
    target_ref = self.GetGlobalTarget(args)
    protocol = self.ConstructProtocol(args)

    address = self._ResolveAddress(
        args, compute_flags.compute_scope.ScopeEnum.GLOBAL)

    forwarding_rule = self.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=address,
        IPProtocol=protocol,
        portRange=port_range,
        target=target_ref.SelfLink())
    if args.load_balancing_scheme == 'INTERNAL':
      forwarding_rule.loadBalancingScheme = (
          self.messages.ForwardingRule
          .LoadBalancingSchemeValueValuesEnum.INTERNAL)

    request = self.messages.ComputeGlobalForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule,
        project=self.project)

    return [request]

  def _CreateRegionalRequests(self, args, forwarding_rule_ref):
    """Create a regionally scoped request."""
    target_ref, region_ref = self.GetRegionalTarget(args, forwarding_rule_ref)
    if not args.region and region_ref:
      args.region = region_ref
    protocol = self.ConstructProtocol(args)

    address = self._ResolveAddress(
        args, compute_flags.compute_scope.ScopeEnum.REGION)

    forwarding_rule = self.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=address,
        IPProtocol=protocol)
    if args.load_balancing_scheme == 'INTERNAL':
      forwarding_rule.loadBalancingScheme = (
          self.messages.ForwardingRule
          .LoadBalancingSchemeValueValuesEnum.INTERNAL)
      forwarding_rule.portRange = args.port_range
    else:
      forwarding_rule.portRange = (
          _ResolvePortRange(args.port_range, args.ports))

    if target_ref.Collection() == 'compute.regionBackendServices':
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
    if hasattr(args, 'service_label'):
      forwarding_rule.serviceLabel = args.service_label
    request = self.messages.ComputeForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule,
        project=self.project,
        region=forwarding_rule_ref.region)

    return [request]

  def _ResolveAddress(self, args, scope):
    # Address takes either an ip address or an address resource. If parsing as
    # an IP address fails, then we resolve as a resource.
    address = args.address
    if address is not None:
      try:
        ipaddr.IPAddress(args.address)
      except ValueError:
        address_ref = flags.ADDRESS_ARG.ResolveAsResource(
            args, self.resources,
            default_scope=scope)
        address = address_ref.SelfLink()

    return address


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    _Args(parser, include_beta=True, include_alpha=False)
    flags.ADDRESS_ARG.AddArgument(parser)
    cls.FORWARDING_RULE_ARG.AddArgument(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULE_ARG = flags.ForwardingRuleArgument()
    _Args(parser, include_beta=True, include_alpha=True)
    flags.AddAddressesAndIPVersions(parser, required=False)
    cls.FORWARDING_RULE_ARG.AddArgument(parser)

  def ConstructNetworkTier(self, args):
    if args.network_tier:
      return self.messages.ForwardingRule.NetworkTierValueValuesEnum(
          args.network_tier)
    else:
      return

  def _CreateGlobalRequests(self, args, forwarding_rule_ref):
    """Create a globally scoped request."""
    port_range = _ResolvePortRange(args.port_range, args.ports)
    if not port_range:
      raise exceptions.ToolException(
          '[--ports] is required for global forwarding rules.')
    target_ref = self.GetGlobalTarget(args)
    protocol = self.ConstructProtocol(args)
    network_tier = self.ConstructNetworkTier(args)

    if args.address is None or args.ip_version:
      ip_version = self.messages.ForwardingRule.IpVersionValueValuesEnum(
          args.ip_version or 'IPV4')
    else:
      ip_version = None

    address = self._ResolveAddress(
        args, compute_flags.compute_scope.ScopeEnum.GLOBAL)

    forwarding_rule = self.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=address,
        IPProtocol=protocol,
        portRange=port_range,
        target=target_ref.SelfLink(),
        ipVersion=ip_version,
        networkTier=network_tier)
    if args.load_balancing_scheme == 'INTERNAL':
      forwarding_rule.loadBalancingScheme = (
          self.messages.ForwardingRule
          .LoadBalancingSchemeValueValuesEnum.INTERNAL)

    request = self.messages.ComputeGlobalForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule,
        project=self.project)

    return [request]

  def _CreateRegionalRequests(self, args, forwarding_rule_ref):
    """Create a regionally scoped request."""
    target_ref, region_ref = self.GetRegionalTarget(args, forwarding_rule_ref)
    if not args.region and region_ref:
      args.region = region_ref
    protocol = self.ConstructProtocol(args)
    network_tier = self.ConstructNetworkTier(args)

    address = self._ResolveAddress(
        args, compute_flags.compute_scope.ScopeEnum.REGION)

    forwarding_rule = self.messages.ForwardingRule(
        description=args.description,
        name=forwarding_rule_ref.Name(),
        IPAddress=address,
        IPProtocol=protocol,
        networkTier=network_tier)
    if args.load_balancing_scheme == 'INTERNAL':
      forwarding_rule.loadBalancingScheme = (
          self.messages.ForwardingRule
          .LoadBalancingSchemeValueValuesEnum.INTERNAL)
      forwarding_rule.portRange = args.port_range
    else:
      forwarding_rule.portRange = (
          _ResolvePortRange(args.port_range, args.ports))

    if target_ref.Collection() == 'compute.regionBackendServices':
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
    if hasattr(args, 'service_label'):
      forwarding_rule.serviceLabel = args.service_label
    request = self.messages.ComputeForwardingRulesInsertRequest(
        forwardingRule=forwarding_rule,
        project=self.project,
        region=forwarding_rule_ref.region)

    return [request]


Create.detailed_help = {
    'DESCRIPTION': ("""\
        *{{command}}* is used to create a forwarding rule. {overview}

        When creating a forwarding rule, exactly one of  ``--target-instance'',
        ``--target-pool'', ``--target-http-proxy'', ``--target-https-proxy'',
        ``--target-ssl-proxy'', or ``--target-vpn-gateway'' must be specified.
        """.format(overview=flags.FORWARDING_RULES_OVERVIEW)),
}

CreateAlpha.detailed_help = {
    'DESCRIPTION': ("""\
        *{{command}}* is used to create a forwarding rule. {overview}

        When creating a forwarding rule, exactly one of  ``--target-instance'',
        ``--target-pool'', ``--target-http-proxy'', ``--target-https-proxy'',
        ``--target-ssl-proxy'', ``--target-tcp-proxy'', or
        ``--target-vpn-gateway'' must be specified.""".format(
            overview=flags.FORWARDING_RULES_OVERVIEW)),
}


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
