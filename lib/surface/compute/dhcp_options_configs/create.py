# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command for creating DHCP options configs."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.dhcp_options_configs import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Google Compute Engine DHCP options configuration."""

  detailed_help = {
      'brief': 'Create a Google Compute Engine DHCP options configuration.',
      'DESCRIPTION': (
          """\
      *{command}* is used to create a regional DHCP options configuration.
      DHCP options configurations store user-defined DHCP parameters such as custom DNS servers,
      NTP servers, domain search suffixes, lease durations, and TFTP/PXE boot parameters.
      """
      ),
      'EXAMPLES': (
          """\
      To create a DHCP options config with custom DNS servers and domain suffix, run:

        $ {command} my-dhcp-config --region=us-central1 --domain-name=corp.example.com --dns-server-ipv4-addresses=192.168.1.10,192.168.1.11
      """
      ),
  }

  DHCP_OPTIONS_CONFIG_ARG = None

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    cls.DHCP_OPTIONS_CONFIG_ARG = flags.DhcpOptionsConfigArgument()
    cls.DHCP_OPTIONS_CONFIG_ARG.AddArgument(parser, operation_type='create')

    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    parser.display_info.AddCacheUpdater(flags.DhcpOptionsConfigsCompleter)

    flags.AddDescription(parser)
    flags.AddLeaseTime(parser)
    flags.AddDomainName(parser)
    flags.AddDnsServerIpv4Addresses(parser)
    flags.AddDnsServerIpv6Addresses(parser)
    flags.AddDnsSearchPaths(parser)
    flags.AddNtpServerIpv4Addresses(parser)
    flags.AddNtpServerIpv6Addresses(parser)
    flags.AddTftpServerName(parser)
    flags.AddTftpServerIpv4Addresses(parser)
    flags.AddBootFileName(parser)
    flags.AddBootFileUrl(parser)
    flags.AddBootFileParams(parser)

  def Run(self, args):
    """Issue a DhcpOptionsConfig INSERT request."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    dhcp_config_ref = self.DHCP_OPTIONS_CONFIG_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.REGION
    )

    dhcp_options_config = client.messages.DhcpOptionsConfig(
        name=dhcp_config_ref.Name(),
        description=args.description,
        leaseTimeSec=args.lease_time,
        domainName=args.domain_name,
        dnsServerIpv4Addresses=args.dns_server_ipv4_addresses or [],
        dnsServerIpv6Addresses=args.dns_server_ipv6_addresses or [],
        dnsSearchPaths=args.dns_search_paths or [],
        ntpServerIpv4Addresses=args.ntp_server_ipv4_addresses or [],
        ntpServerIpv6Addresses=args.ntp_server_ipv6_addresses or [],
        tftpServerIpv4Name=args.tftp_server_name,
        tftpServerIpv4Addresses=args.tftp_server_ipv4_addresses or [],
        bootFileIpv4Name=args.boot_file_name,
        bootFileIpv6Url=args.boot_file_url,
        bootFileIpv6Parameters=args.boot_file_params or [],
    )

    request = client.messages.ComputeDhcpOptionsConfigsInsertRequest(
        project=dhcp_config_ref.project,
        region=dhcp_config_ref.region,
        dhcpOptionsConfig=dhcp_options_config,
    )

    collection = client.apitools_client.dhcpOptionsConfigs
    return client.MakeRequests([(collection, 'Insert', request)])
