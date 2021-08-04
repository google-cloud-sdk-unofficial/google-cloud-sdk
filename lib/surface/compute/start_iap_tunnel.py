# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Implements the command for starting a tunnel with Cloud IAP."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute import iap_tunnel
from googlecloudsdk.command_lib.compute import scope
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


_CreateTargetArgs = collections.namedtuple('_TargetArgs', [
    'project', 'zone', 'instance', 'interface', 'port', 'region', 'network',
    'ip'
])

_ON_PREM_EXTRA_DESCRIPTION = """

If the `--region` and `--network` flags are provided, then an IP address must be
supplied instead of an instance name. This is most useful for connecting to
on-prem resources.
"""

_ON_PREM_EXTRA_EXAMPLES = """

To use the IP address of your remote VM (eg, for on-prem), you must also specify
the `--region` and `--network` flags:

  $ {command} 10.1.2.3 3389 --region=us-central1 --network=default
"""


def _DetailedHelp(version):
  """Construct help text based on the command release track."""
  detailed_help = {
      'brief': 'Starts an IAP TCP forwarding tunnel.',
      'DESCRIPTION': """\
Starts a tunnel to Cloud Identity-Aware Proxy for TCP forwarding through which
another process can create a connection (eg. SSH, RDP) to a Google Compute
Engine instance.

To learn more, see the
[IAP for TCP forwarding documentation](https://cloud.google.com/iap/docs/tcp-forwarding-overview).
""",
      'EXAMPLES': """\
To open a tunnel to the instances's RDP port on an arbitrary local port, run:

  $ {command} my-instance 3389

To open a tunnel to the instance's RDP port on a specific local port, run:

  $ {command} my-instance 3389 --local-host-port=localhost:3333
"""
  }

  if version == 'ALPHA':
    detailed_help['DESCRIPTION'] += _ON_PREM_EXTRA_DESCRIPTION
    detailed_help['EXAMPLES'] += _ON_PREM_EXTRA_EXAMPLES

  return detailed_help


@base.ReleaseTracks(base.ReleaseTrack.GA)
class StartIapTunnel(base.Command):
  """Starts an IAP TCP forwarding tunnel."""

  enable_ip_based_flags = False

  @classmethod
  def Args(cls, parser):
    iap_tunnel.AddProxyServerHelperArgs(parser)
    flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        'instance_port',
        type=arg_parsers.BoundedInt(lower_bound=1, upper_bound=65535),
        help="The name or number of the instance's port to connect to.")

    local_host_port_help_text = """\
`LOCAL_HOST:LOCAL_PORT` on which gcloud should bind and listen for connections
that should be tunneled.

`LOCAL_PORT` may be omitted, in which case it is treated as 0 and an arbitrary
unused local port is chosen. The colon also may be omitted in that case.

If `LOCAL_PORT` is 0, an arbitrary unused local port is chosen."""
    parser.add_argument(
        '--local-host-port',
        type=lambda arg: arg_parsers.HostPort.Parse(arg, ipv6_enabled=True),
        default='localhost:0',
        help=local_host_port_help_text)

    # It would be logical to put --local-host-port and --listen-on-stdin in a
    # mutex group, but then the help text would display a message saying "At
    # most one of these may be specified" even though it only shows
    # --local-host-port.
    parser.add_argument(
        '--listen-on-stdin',
        action='store_true',
        hidden=True,
        help=('Whether to get/put local data on stdin/stdout instead of '
              'listening on a socket.  It is an error to specify '
              '--local-host-port with this, because that flag has no meaning '
              'with this.'))
    parser.add_argument(
        '--iap-tunnel-disable-connection-check',
        default=False,
        action='store_true',
        help='Disables the immediate check of the connection.')

    if cls.enable_ip_based_flags:
      iap_tunnel.AddIpBasedTunnelArgs(parser)

  def Run(self, args):
    if args.listen_on_stdin and args.IsSpecified('local_host_port'):
      raise calliope_exceptions.ConflictingArgumentsException(
          '--listen-on-stdin', '--local-host-port')
    target = self._GetTargetArgs(args)

    if args.listen_on_stdin:
      iap_tunnel_helper = iap_tunnel.IapTunnelStdinHelper(args, target.project)
    else:
      local_host, local_port = self._GetLocalHostPort(args)
      check_connection = True
      if hasattr(args, 'iap_tunnel_disable_connection_check'):
        check_connection = not args.iap_tunnel_disable_connection_check
      iap_tunnel_helper = iap_tunnel.IapTunnelProxyServerHelper(
          args, target.project, local_host, local_port, check_connection)

    if target.ip:
      iap_tunnel_helper.ConfigureForIP(target.region, target.network, target.ip,
                                       target.port)
    else:
      iap_tunnel_helper.ConfigureForInstance(target.zone, target.instance,
                                             target.interface, target.port)

    iap_tunnel_helper.Run()

  def _GetTargetArgs(self, args):
    # TODO(b/190426150): change to just "IsSpecified" when going to GA
    if args.IsKnownAndSpecified('network') and args.IsKnownAndSpecified(
        'region'):
      return _CreateTargetArgs(
          project=properties.VALUES.core.project.GetOrFail(),
          region=args.region,
          network=args.network,
          # TODO(b/190426150): validate IPv4 format
          ip=args.instance_name,
          port=args.instance_port,
          zone=None,
          instance=None,
          interface=None)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    ssh_helper = ssh_utils.BaseSSHCLIHelper()

    instance_ref = flags.SSH_INSTANCE_RESOLVER.ResolveResources(
        [args.instance_name], scope.ScopeEnum.ZONE, args.zone, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))[0]
    instance_obj = ssh_helper.GetInstance(client, instance_ref)

    return _CreateTargetArgs(
        project=instance_ref.project,
        zone=instance_ref.zone,
        instance=instance_obj.name,
        interface=ssh_utils.GetInternalInterface(instance_obj).name,
        port=args.instance_port,
        region=None,
        network=None,
        ip=None)

  def _GetLocalHostPort(self, args):
    local_host_arg = args.local_host_port.host or 'localhost'
    port_arg = (
        int(args.local_host_port.port) if args.local_host_port.port else 0)
    local_port = iap_tunnel.DetermineLocalPort(port_arg=port_arg)
    if not port_arg:
      log.status.Print('Picking local unused port [%d].' % local_port)
    return local_host_arg, local_port


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class StartIapTunnelBeta(StartIapTunnel):
  """Starts an IAP TCP forwarding tunnel (Beta)."""
  enable_ip_based_flags = False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class StartIapTunnelAlpha(StartIapTunnelBeta):
  """Starts an IAP TCP forwarding tunnel (Alpha)."""
  enable_ip_based_flags = True


StartIapTunnelAlpha.detailed_help = _DetailedHelp('ALPHA')
StartIapTunnelBeta.detailed_help = _DetailedHelp('BETA')
StartIapTunnel.detailed_help = _DetailedHelp('GA')
