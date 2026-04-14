# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Convenience functions for dealing with alias IP ranges."""


from googlecloudsdk.calliope import exceptions as calliope_exceptions

_INVALID_FORMAT_MESSAGE_FOR_INSTANCE = (
    'An alias IP range must contain range name and IP range separated by '
    'a colon, or only the IP range.  The IP range portion can be '
    'expressed as a full IP CIDR range (e.g. 10.1.1.0/24), or a single IP '
    'address (e.g. 10.1.1.1), or an IP CIDR net mask (e.g. /24)'
)

_INVALID_FORMAT_MESSAGE_FOR_INSTANCE_TEMPLATE = (
    'An alias IP range must contain range name and IP CIDR net mask (e.g. '
    '/24) separated by a colon, or only the IP CIDR net mask (e.g. /24).'
)

_INVALID_FORMAT_MESSAGE_FOR_INSTANCE_IPV4 = (
    'An alias IP range must contain range name and IP range separated by a '
    'colon (:) or an equals sign (=), or only the IP range. The IP range '
    'portion can be expressed as a full IP CIDR range (e.g. 10.1.1.0/24), or '
    'a single IP address (e.g. 10.1.1.1), or an IP CIDR net mask (e.g. /24).'
)

_INVALID_FORMAT_MESSAGE_FOR_INSTANCE_TEMPLATE_IPV4 = (
    'An alias IP range must contain range name and IP CIDR net mask (e.g. '
    '/24) separated by a colon (:) or an equals sign (=), or only the IP CIDR '
    'net mask (e.g. /24).'
)

_INVALID_FORMAT_MESSAGE_FOR_INSTANCE_IPV6 = (
    'An alias IPv6 range must contain range name and IP range separated by an '
    'equals sign (=), or only the IP range. The IP range portion can be '
    'expressed as a full IPv6 CIDR range (e.g., 2001:db8:1:1::/96) or an IP '
    'CIDR net mask (e.g., /96).'
)

_INVALID_FORMAT_MESSAGE_FOR_INSTANCE_TEMPLATE_IPV6 = (
    'An alias IPv6 range must contain range name and IP CIDR net mask (e.g.,'
    ' /96) separated by an equals sign (=), or only the IP CIDR net mask (e.g.,'
    ' /96).'
)


# TODO(b/497760754): Remove once support_alias_ipv6_ranges is cleaned up.
def CreateAliasIpRangeMessagesFromStringOld(
    messages, instance, alias_ip_ranges_string
):
  """Returns a list of AliasIpRange messages by parsing the input string.

  Args:
    messages: GCE API messages.
    instance: If True, this call is for parsing instance flags; otherwise
        it is for instance template.
    alias_ip_ranges_string: Command line string that specifies a list of
        alias IP ranges. Alias IP ranges are separated by semicolons.
        Each alias IP range has the format <alias-ip-range> or
        {range-name}:<alias-ip-range>.  The range-name is the name of the
        range within the network interface's subnet from which to allocate
        an alias range. alias-ip-range can be a CIDR range, an IP address,
        or a net mask (e.g. "/24"). Note that the validation is done on
        the server. This method just creates the request message by parsing
        the input string.
        Example string:
        "/24;range2:192.168.100.0/24;range3:192.168.101.0/24"

  Returns:
    A list of AliasIpRange messages.
  """
  if not alias_ip_ranges_string:
    return []
  alias_ip_range_strings = alias_ip_ranges_string.split(';')
  return [_CreateAliasIpRangeMessageFromString(messages, instance, s) for
          s in alias_ip_range_strings]


def CreateAliasIpRangeMessagesFromString(
    messages, instance, alias_ip_ranges_string
):
  """Returns a list of AliasIpRange messages by parsing the input string.

  Args:
    messages: GCE API messages.
    instance: If True, this call is for parsing instance flags; otherwise it is
      for instance template.
    alias_ip_ranges_string: Command line string that specifies a list of alias
      IPv6 ranges. Alias IPv6 ranges are separated by semicolons. Each alias
      IPv6 range has the format <alias-ipv6-range> or
      {range-name}=<alias-ipv6-range>. The range-name is the name of the range
      within the network interface's subnet from which to allocate an alias
      range. alias-ipv6-range can be a CIDR range (e.g., 2001:db8:1::/96) or a
      prefix length (e.g., /96). Note that the validation is done on the server.
      This method just creates the request message by parsing the input string.
      Example string "/96;range2=2001:db8:1::/96;range3=2001:db8:2::/96"

  Returns:
    A list of AliasIpRange messages.
  """
  try:
    return _CreateAliasIpRangeMessagesFromStringWithDelimiters(
        messages, alias_ip_ranges_string, [':', '=']
    )
  except ValueError:
    raise calliope_exceptions.InvalidArgumentException(
        'aliases',
        _INVALID_FORMAT_MESSAGE_FOR_INSTANCE_IPV4
        if instance
        else _INVALID_FORMAT_MESSAGE_FOR_INSTANCE_TEMPLATE_IPV4,
    ) from None


def CreateAliasIpv6RangeMessagesFromString(
    messages, instance, alias_ip_ranges_string
):
  """Returns a list of AliasIpRange messages by parsing the input string.

  Args:
    messages: GCE API messages.
    instance: If True, this call is for parsing instance flags; otherwise it is
      for instance template.
    alias_ip_ranges_string: Command line string that specifies a list of alias
      IP ranges. Alias IP ranges are separated by semicolons. Each alias IP
      range has the format <alias-ip-range> or {range-name}:<alias-ip-range> or
      {range-name}=<alias-ip-range>. The range-name is the name of the range
      within the network interface's subnet from which to allocate an alias
      range. alias-ip-range can be a CIDR range, an IP address, or a net mask
      (e.g. "/24"). Note that the validation is done on the server. This method
      just creates the request message by parsing the input string. Example
      string "/24;range2=192.168.100.0/24;range3:192.168.101.0/24"

  Returns:
    A list of AliasIpRange messages.
  """
  try:
    return _CreateAliasIpRangeMessagesFromStringWithDelimiters(
        messages, alias_ip_ranges_string, ['=']
    )
  except ValueError:
    raise calliope_exceptions.InvalidArgumentException(
        'ipv6-aliases',
        _INVALID_FORMAT_MESSAGE_FOR_INSTANCE_IPV6
        if instance
        else _INVALID_FORMAT_MESSAGE_FOR_INSTANCE_TEMPLATE_IPV6,
    ) from None


def _CreateAliasIpRangeMessageFromString(
    messages, instance, alias_ip_range_string):
  """Returns a new AliasIpRange message by parsing the input string."""
  alias_ip_range = messages.AliasIpRange()

  tokens = alias_ip_range_string.split(':')
  if len(tokens) == 1:
    # Only IP CIDR is specified.
    alias_ip_range.ipCidrRange = tokens[0]
  elif len(tokens) == 2:
    # Both the range name and the CIDR are specified
    alias_ip_range.subnetworkRangeName = tokens[0]
    alias_ip_range.ipCidrRange = tokens[1]
  else:
    # There are too many or too few tokens.
    raise calliope_exceptions.InvalidArgumentException(
        'aliases',
        _INVALID_FORMAT_MESSAGE_FOR_INSTANCE
        if instance
        else _INVALID_FORMAT_MESSAGE_FOR_INSTANCE_TEMPLATE,
    )
  return alias_ip_range


def _CreateAliasIpRangeMessagesFromStringWithDelimiters(
    messages, alias_ip_ranges_string, delimiter_list
):
  """Returns a list of AliasIpRange messages by parsing the input string.

  Args:
    messages: GCE API messages.
    alias_ip_ranges_string: Command line string that specifies a list of alias
      IP ranges.
    delimiter_list: List of delimiters to use for parsing single alias IP range.

  Returns:
    A list of AliasIpRange messages and a boolean indicating whether the
    parsing was valid.
  """
  if not alias_ip_ranges_string:
    return []
  alias_ip_range_strings = alias_ip_ranges_string.split(';')

  alias_ip_range_messages = []
  for alias_ip_range_string in alias_ip_range_strings:
    alias_ip_range_message = _CreateAliasIpRangeMessageFromStringWithDelimiters(
        messages, alias_ip_range_string, delimiter_list
    )

    alias_ip_range_messages.append(alias_ip_range_message)

  return alias_ip_range_messages


def _CreateAliasIpRangeMessageFromStringWithDelimiters(
    messages, alias_ip_range_string, delimiters
):
  """Returns a new AliasIpRange message by parsing the input string.

  Args:
    messages: GCE API messages.
    alias_ip_range_string: Command line string that specifies an alias IP range.
    delimiters: List of delimiters to use for parsing.

  Returns:
    An AliasIpRange message and a boolean indicating whether the
    parsing was valid.
  """
  # Find the delimiter in the string if none of the delimiters are in the
  # string, use the first delimiter.
  delimiter = delimiters[0]
  for d in delimiters:
    if d in alias_ip_range_string:
      delimiter = d
      break

  tokens = alias_ip_range_string.split(delimiter)
  if len(tokens) == 1:
    # Only IP CIDR is specified.
    return messages.AliasIpRange(ipCidrRange=tokens[0])
  elif len(tokens) == 2:
    # Both the range name and the CIDR are specified
    return messages.AliasIpRange(
        subnetworkRangeName=tokens[0], ipCidrRange=tokens[1]
    )

  else:
    # There are too many or too few tokens.
    raise ValueError(
        'Invalid alias IP range string: {}'.format(alias_ip_range_string)
    )
