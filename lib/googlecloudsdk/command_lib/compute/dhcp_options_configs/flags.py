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
"""Flags and helpers for the compute dhcp-options-configs commands."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      region.basename(),
      domainName,
      dnsServerIpv4Addresses.list():label=DNS_SERVERS,
      ntpServerIpv4Addresses.list():label=NTP_SERVERS,
      leaseTimeSec
    )"""


class DhcpOptionsConfigsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(DhcpOptionsConfigsCompleter, self).__init__(
        collection='compute.dhcpOptionsConfigs',
        list_command='alpha compute dhcp-options-configs list --uri',
        **kwargs
    )


def AddDescription(parser):
  """Add support for --description flag."""
  parser.add_argument(
      '--description',
      default=None,
      help='An optional, textual description for the DHCP options config.',
  )


def AddLeaseTime(parser):
  """Add support for --lease-time flag."""
  parser.add_argument(
      '--lease-time',
      type=arg_parsers.Duration(default_unit='s'),
      default=None,
      help="""\
      The duration of the IPv4 address lease offered by the DHCP server to
      the client VM. See $ gcloud topic datetimes for information on
      duration formats (e.g. 24h, 86400s, 60m). Corresponds to DHCPv4 Option 51.
      """,
  )


def AddDomainName(parser):
  """Add support for --domain-name flag."""
  parser.add_argument(
      '--domain-name',
      default=None,
      help='The primary DNS domain name suffix (Option 15).',
  )


def AddDnsServerIpv4Addresses(parser):
  """Add support for --dns-server-ipv4-addresses flag."""
  parser.add_argument(
      '--dns-server-ipv4-addresses',
      type=arg_parsers.ArgList(),
      metavar='DNS_SERVER_IPV4_ADDRESSES',
      default=None,
      help='List of IPv4 addresses of recursive DNS servers (Option 6).',
  )


def AddDnsServerIpv6Addresses(parser):
  """Add support for --dns-server-ipv6-addresses flag."""
  parser.add_argument(
      '--dns-server-ipv6-addresses',
      type=arg_parsers.ArgList(),
      metavar='DNS_SERVER_IPV6_ADDRESSES',
      default=None,
      help='List of IPv6 addresses of recursive DNS servers (Option 23).',
  )


def AddDnsSearchPaths(parser):
  """Add support for --dns-search-paths flag."""
  parser.add_argument(
      '--dns-search-paths',
      type=arg_parsers.ArgList(),
      metavar='DNS_SEARCH_PATHS',
      default=None,
      help='List of domain search suffixes (Options 119 and 24).',
  )


def AddNtpServerIpv4Addresses(parser):
  """Add support for --ntp-server-ipv4-addresses flag."""
  parser.add_argument(
      '--ntp-server-ipv4-addresses',
      type=arg_parsers.ArgList(),
      metavar='NTP_SERVER_IPV4_ADDRESSES',
      default=None,
      help='List of IPv4 addresses of NTP servers (Option 42).',
  )


def AddNtpServerIpv6Addresses(parser):
  """Add support for --ntp-server-ipv6-addresses flag."""
  parser.add_argument(
      '--ntp-server-ipv6-addresses',
      type=arg_parsers.ArgList(),
      metavar='NTP_SERVER_IPV6_ADDRESSES',
      default=None,
      help='List of IPv6 addresses of NTP servers (Option 56).',
  )


def AddTftpServerName(parser):
  """Add support for --tftp-server-name flag."""
  parser.add_argument(
      '--tftp-server-name',
      default=None,
      help='Hostname of the TFTP boot server (Option 66).',
  )


def AddTftpServerIpv4Addresses(parser):
  """Add support for --tftp-server-ipv4-addresses flag."""
  parser.add_argument(
      '--tftp-server-ipv4-addresses',
      type=arg_parsers.ArgList(),
      metavar='TFTP_SERVER_IPV4_ADDRESSES',
      default=None,
      help='List of IPv4 addresses of TFTP boot servers (Option 150).',
  )


def AddBootFileName(parser):
  """Add support for --boot-file-name flag."""
  parser.add_argument(
      '--boot-file-name',
      default=None,
      help='File path of the TFTP boot file (Option 67).',
  )


def AddBootFileUrl(parser):
  """Add support for --boot-file-url flag."""
  parser.add_argument(
      '--boot-file-url',
      default=None,
      help='URL of the IPv6 boot file (Option 59).',
  )


def AddBootFileParams(parser):
  """Add support for --boot-file-params flag."""
  parser.add_argument(
      '--boot-file-params',
      type=arg_parsers.ArgList(),
      metavar='BOOT_FILE_PARAMS',
      default=None,
      help='Boot file parameter arguments for IPv6 (Option 60).',
  )


def DhcpOptionsConfigArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='dhcp options config',
      completer=DhcpOptionsConfigsCompleter,
      plural=plural,
      required=required,
      regional_collection='compute.dhcpOptionsConfigs',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION,
  )
