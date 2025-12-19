# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Command to download an installation script for a Monitoring Point."""

from urllib import parse
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.Hidden
class DownloadInstallScript(base.Command):
  """Download an installation script for a Monitoring Point."""

  detailed_help = {
      'BRIEF': 'Download an installation script for a Monitoring Point.',
      'DESCRIPTION': """\
          Downloads an installation script for a Monitoring Point for a given
          Network Monitoring Provider.

          The `--network-monitoring-provider`, `--location`, `--monitoring-point-type`,
          and `--hostname` arguments are required for all Monitoring Points.
          Additional arguments depend on the value of `--monitoring-point-type`.

          If `--monitoring-point-type=container` is specified, no other flags
          are required, and flags like `--password`, `--time-zone`,
          `--use-dhcp`, and `--static-ip-address` are not allowed.

          If `--monitoring-point-type=kvm` or `--monitoring-point-type=vmware`
          is specified, `--password` and `--time-zone` are also required.
          You must also specify either `--use-dhcp` for DHCP configurations or
          `--static-ip-address` for static IP configurations. If using
          `--static-ip-address`, `--gateway-address` and `--dns-server-address`
          are also required.
          """,
      'EXAMPLES': """\
          To download the install script for a Monitoring Point of type `container`, run:

            $ {command} --network-monitoring-provider=my-provider --location=global --monitoring-point-type=container --hostname=test-container

          To download the install script for a Monitoring Point of type `kvm` using DHCP, run:

            $ {command} --network-monitoring-provider=my-provider --location=global --monitoring-point-type=kvm --hostname=test-kvm --password=my-password --time-zone=America/Los_Angeles --use-dhcp

          To download the install script for a Monitoring Point of type `vmware` using a static IP, run:

            $ {command} --network-monitoring-provider=my-provider --location=global --monitoring-point-type=vmware --hostname=test-vmware --password=my-password --time-zone=America/Los_Angeles --static-ip-address=192.168.1.100 --netmask=255.255.255.0 --gateway-address=192.168.1.1 --dns-server-address=8.8.8.8
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--network-monitoring-provider',
        required=True,
        help='The ID of the Network Monitoring Provider.',
    )
    parser.add_argument(
        '--location',
        required=True,
        help=(
            'The location of the Network Monitoring Provider (example:,'
            ' `global`).'
        ),
    )
    parser.add_argument(
        '--monitoring-point-type',
        required=True,
        choices=['container', 'kvm', 'vmware'],
        help='The type of the Monitoring Point.',
    )
    parser.add_argument(
        '--hostname',
        required=True,
        help='The hostname of the Monitoring Point (example: `test-vm`).',
    )
    parser.add_argument(
        '--password',
        help=(
            'Password for logging into the Monitoring Point. Required for'
            ' types KVM and VMWARE, not allowed for CONTAINER.'
        ),
    )
    parser.add_argument(
        '--time-zone',
        help=(
            'Time zone ID for the Monitoring Point (example: '
            ' `America/Los_Angeles`). Required for types KVM and VMWARE, not'
            ' allowed for CONTAINER.'
        ),
    )
    parser.add_argument(
        '--use-dhcp',
        action='store_true',
        help=(
            'Whether to use DHCP for IP address configuration. Allowed for'
            ' types KVM and VMWARE only.'
        ),
    )

    static_ip_group = parser.add_group(
        help=(
            'Static IP address configuration. Allowed for types KVM and VMWARE'
            ' only.'
        )
    )
    static_ip_group.add_argument(
        '--static-ip-address',
        help=(
            'Static IP address of the Monitoring Point. If specified,'
            ' `--gateway-address` and `--dns-server-address` are required.'
        ),
    )
    static_ip_group.add_argument(
        '--netmask',
        help=(
            'Network mask (example: "255.255.255.0"). Used'
            ' with `--static-ip-address`.'
        ),
    )
    static_ip_group.add_argument(
        '--gateway-address',
        help=(
            'Gateway IP address. Required if `--static-ip-address` is'
            ' specified.'
        ),
    )
    static_ip_group.add_argument(
        '--dns-server-address',
        help=(
            'Primary DNS server address. Required if `--static-ip-address` is'
            ' specified.'
        ),
    )
    static_ip_group.add_argument(
        '--dns-server-secondary-address',
        help='Secondary DNS server address. Used with `--static-ip-address`.',
    )
    static_ip_group.add_argument(
        '--domain',
        help=(
            'Domain name of the Monitoring Point. Used with'
            ' `--static-ip-address`.'
        ),
    )

    parser.add_argument(
        '--ntp-server-address',
        help=(
            'Primary NTP server address (IP address or FQDN). Allowed for'
            ' types KVM and VMWARE only.'
        ),
    )
    parser.add_argument(
        '--ntp-server-secondary-address',
        help=(
            'Secondary NTP server address (IP address or FQDN). Allowed for'
            ' types KVM and VMWARE only.'
        ),
    )

  def _ValidateArgs(self, args):
    """Validates argument combinations based on monitoring_point_type."""
    mp_type = args.monitoring_point_type.upper()

    if mp_type == 'CONTAINER':
      illegal_container_args = [
          'password',
          'time_zone',
          'use_dhcp',
          'static_ip_address',
          'netmask',
          'gateway_address',
          'dns_server_address',
          'dns_server_secondary_address',
          'domain',
          'ntp_server_address',
          'ntp_server_secondary_address',
      ]
      for arg_name in illegal_container_args:
        if args.IsSpecified(arg_name):
          arg_name_dash = arg_name.replace('_', '-')
          raise exceptions.InvalidArgumentException(
              arg_name_dash,
              f'{arg_name_dash} is not allowed for type CONTAINER',
          )
    elif mp_type in ['KVM', 'VMWARE']:
      if not args.IsSpecified('time_zone'):
        raise exceptions.RequiredArgumentException(
            'time-zone', f'Time zone is required for type {mp_type}'
        )
      if not args.IsSpecified('password'):
        raise exceptions.RequiredArgumentException(
            'password', f'Password is required for type {mp_type}'
        )

      has_use_dhcp = args.IsSpecified('use_dhcp')
      has_static_ip = args.IsSpecified('static_ip_address')

      if not (has_use_dhcp or has_static_ip):
        raise exceptions.OneOfArgumentsRequiredException(
            ['--use-dhcp', '--static-ip-address'],
            'Specify either --use-dhcp or --static-ip-address for type'
            f' {mp_type}.',
        )
      if has_use_dhcp and has_static_ip:
        raise exceptions.ConflictingArgumentsException(
            '--use-dhcp', '--static-ip-address'
        )

      if has_static_ip:
        if not args.IsSpecified('gateway_address'):
          raise exceptions.RequiredArgumentException(
              'gateway-address',
              '`--gateway-address` is required when `--static-ip-address` is'
              ' specified',
          )
        if not args.IsSpecified('dns_server_address'):
          raise exceptions.RequiredArgumentException(
              'dns-server-address',
              '`--dns-server-address` is required when `--static-ip-address`'
              ' is specified',
          )
    else:
      # This case should not be reached if choices in Args are enforced
      raise exceptions.InvalidArgumentException(
          'monitoring-point-type',
          f'Invalid monitoringPointType: {args.monitoring_point_type}',
      )

  def Run(self, args):
    self._ValidateArgs(args)

    project = properties.VALUES.core.project.Get(required=True)
    location = args.location
    provider_id = args.network_monitoring_provider
    release_track = self.ReleaseTrack()
    if release_track == base.ReleaseTrack.ALPHA:
      api_version = 'v1alpha1'
    else:
      api_version = 'v1'

    parent = f'projects/{project}/locations/{location}/networkMonitoringProviders/{provider_id}'
    request_path = (
        f'{api_version}/{parent}/monitoringPoints:downloadInstallScript'
    )

    query_params = [
        ('hostname', args.hostname),
        ('monitoringPointType', args.monitoring_point_type.upper()),
    ]
    if args.IsSpecified('password'):
      query_params.append(('password', args.password))
    if args.IsSpecified('time_zone'):
      query_params.append(('timeZone.id', args.time_zone))
    if args.IsSpecified('use_dhcp'):
      query_params.append(('useDhcp', args.use_dhcp))
    if args.IsSpecified('static_ip_address'):
      query_params.append(('staticIpAddress.ipAddress', args.static_ip_address))
    if args.IsSpecified('netmask'):
      query_params.append(('staticIpAddress.netmask', args.netmask))
    if args.IsSpecified('gateway_address'):
      query_params.append(
          ('staticIpAddress.gatewayAddress', args.gateway_address)
      )
    if args.IsSpecified('dns_server_address'):
      query_params.append(
          ('staticIpAddress.dnsServerAddress', args.dns_server_address)
      )
    if args.IsSpecified('dns_server_secondary_address'):
      query_params.append((
          'staticIpAddress.dnsServerSecondaryAddress',
          args.dns_server_secondary_address,
      ))
    if args.IsSpecified('domain'):
      query_params.append(('staticIpAddress.domain', args.domain))
    if args.IsSpecified('ntp_server_address'):
      query_params.append(('ntpServerAddress', args.ntp_server_address))
    if args.IsSpecified('ntp_server_secondary_address'):
      query_params.append(
          ('ntpServerSecondaryAddress', args.ntp_server_secondary_address)
      )

    encoded_params = parse.urlencode(query_params)
    client = apis.GetClientInstance('networkmanagement', api_version)
    base_uri = apis.GetEffectiveApiEndpoint('networkmanagement', api_version)
    uri = f'{base_uri}{request_path}?{encoded_params}'
    http = client.http

    response, body = http.request(
        uri,
        method='GET',
        headers={},
    )

    if response.status != 200:
      raise exceptions.HttpException(
          f'API request failed with status {response.status}: {body}'
      )

    log.out.write(body)
    return None
