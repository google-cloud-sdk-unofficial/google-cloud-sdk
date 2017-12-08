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
from googlecloudsdk.command_lib.compute.forwarding_rules import flags
from googlecloudsdk.core import apis as core_apis
from googlecloudsdk.core import log


def _SupportedProtocols(messages):
  return sorted(
      messages.ForwardingRule.IPProtocolValueValuesEnum.to_dict().keys())


def _Args(parser, include_alpha_targets, include_beta_targets):
  """Argument parsing."""
  flags.AddCommonFlags(parser)
  flags.AddUpdateArgs(parser, include_alpha_targets, include_beta_targets)

  address = parser.add_argument(
      '--address',
      help='The external IP address that the forwarding rule will serve.')
  address.detailed_help = """\
      The external IP address that the forwarding rule will
      serve. All traffic sent to this IP address is directed to the
      target pointed to by the forwarding rule. If the address is
      reserved, it must either (1) reside in the global scope if the
      forwarding rule is being configured to point to a target HTTP
      proxy or (2) reside in the same region as the forwarding rule
      if the forwarding rule is being configured to point to a
      target pool or target instance. If this flag is omitted, an
      ephemeral IP address is assigned.
      """
  v1_messages = core_apis.GetMessagesModule('compute', 'v1')
  ip_protocol = parser.add_argument(
      '--ip-protocol',
      choices=_SupportedProtocols(v1_messages),
      type=lambda x: x.upper(),
      help='The IP protocol that the rule will serve.')
  ip_protocol.detailed_help = """\
      The IP protocol that the rule will serve. If left empty, TCP
      is used. Supported protocols are: {0}.
      """.format(', '.join(_SupportedProtocols(v1_messages)))

  parser.add_argument(
      '--description',
      help='An optional textual description for the forwarding rule.')

  ports_scope = parser.add_mutually_exclusive_group()
  ports = ports_scope.add_argument(
      '--ports',
      metavar='[PORT | PORT-PORT]',
      help=('If specified, only packets addressed to the ports or '
            'port ranges will be forwarded.'),
      type=arg_parsers.ArgList(
          min_length=1, element_type=arg_parsers.Range.Parse),
      action=arg_parsers.FloatingListValuesCatcher(),
      default=[])

  ports.detailed_help = """\
          If specified, only packets addressed to ports in the specified
          list will be forwarded. If not specified for regional forwarding
          rules, all ports are matched. This flag is required for global
          forwarding rules and accepts a single continuous set of ports.

          Individual ports and ranges can be specified,
          for example (`--ports 8000-8004` or `--ports 80`).
          """
  port_range = ports_scope.add_argument(
      '--port-range',
      type=arg_parsers.Range.Parse,
      help='DEPRECATED, use --ports. If specified, only packets addressed to '
           'the port or ports in the specified range will be forwarded.',
      metavar='[PORT | PORT-PORT]')
  port_range.detailed_help = """\
      DEPRECATED, use --ports. If specified, only packets addressed to ports in
      the specified range will be forwarded. If not specified for regional
      forwarding rules, all ports are matched. This flag is required for global
      forwarding rules.

      Either an individual port (`--port-range 80`) or a range of ports
      (`--port-range 3000-3100`) may be specified.
      """


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(utils.ForwardingRulesTargetMutator):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  @staticmethod
  def Args(parser):
    _Args(parser, include_alpha_targets=False, include_beta_targets=False)

  @property
  def method(self):
    return 'Insert'

  def ConstructProtocol(self, args):
    if args.ip_protocol:
      return self.messages.ForwardingRule.IPProtocolValueValuesEnum(
          args.ip_protocol)
    else:
      return

  def CreateGlobalRequests(self, args):
    """Create a globally scoped request."""
    port_range = _ResolvePortRange(args.port_range, args.ports)
    if not port_range:
      raise exceptions.ToolException(
          '[--ports] is required for global forwarding rules.')
    target_ref = self.GetGlobalTarget(args)
    forwarding_rule_ref = self.CreateGlobalReference(
        args.name, resource_type='globalForwardingRules')
    protocol = self.ConstructProtocol(args)

    request = self.messages.ComputeGlobalForwardingRulesInsertRequest(
        forwardingRule=self.messages.ForwardingRule(
            description=args.description,
            name=forwarding_rule_ref.Name(),
            IPAddress=args.address,
            IPProtocol=protocol,
            portRange=port_range,
            target=target_ref.SelfLink(),
        ),
        project=self.project)

    return [request]

  def CreateRegionalRequests(self, args):
    """Create a regionally scoped request."""
    target_ref, target_region = self.GetRegionalTarget(args)
    forwarding_rule_ref = self.CreateRegionalReference(
        args.name, args.region or target_region)
    protocol = self.ConstructProtocol(args)

    request = self.messages.ComputeForwardingRulesInsertRequest(
        forwardingRule=self.messages.ForwardingRule(
            description=args.description,
            name=forwarding_rule_ref.Name(),
            IPAddress=args.address,
            IPProtocol=protocol,
            portRange=_ResolvePortRange(args.port_range, args.ports),
            target=target_ref.SelfLink(),
        ),
        project=self.project,
        region=forwarding_rule_ref.region)

    return [request]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  @staticmethod
  def Args(parser):
    _Args(parser, include_alpha_targets=False, include_beta_targets=True)

  def GetGlobalTarget(self, args):
    if args.target_ssl_proxy:
      return self.CreateGlobalReference(
          args.target_ssl_proxy, resource_type='targetSslProxies')
    return super(CreateBeta, self).GetGlobalTarget(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a forwarding rule to direct network traffic to a load balancer."""

  @staticmethod
  def Args(parser):
    _Args(parser, include_alpha_targets=True, include_beta_targets=True)

  def CreateRegionalRequests(self, args):
    """Create a regionally scoped request."""
    target_ref, target_region = self.GetRegionalTarget(args)
    forwarding_rule_ref = self.CreateRegionalReference(
        args.name, args.region or target_region)
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
          forwarding_rule.subnetwork = self.CreateRegionalReference(
              args.subnet, forwarding_rule.region,
              resource_type='subnetworks').SelfLink()
        if args.network is not None:
          forwarding_rule.network = self.CreateGlobalReference(
              args.network, resource_type='networks').SelfLink()
    else:
      forwarding_rule.target = target_ref.SelfLink()
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
        or ``--target-vpn-gateway'' must be specified.
        """.format(overview=flags.FORWARDING_RULES_OVERVIEW)),
}

CreateBeta.detailed_help = {
    'DESCRIPTION': ("""\
        *{{command}}* is used to create a forwarding rule. {overview}

        When creating a forwarding rule, exactly one of  ``--target-instance'',
        ``--target-pool'', ``--target-http-proxy'', ``--target-https-proxy'',
        ``--target-ssl-proxy'', or ``--target-vpn-gateway'' must be specified.
        """.format(overview=flags.FORWARDING_RULES_OVERVIEW)),
}

CreateAlpha.detailed_help = CreateBeta.detailed_help


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

