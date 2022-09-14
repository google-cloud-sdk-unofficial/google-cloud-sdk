# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for update to instance network interfaces."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ipaddress

from googlecloudsdk.api_lib.compute import alias_ip_range_utils
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import utils as api_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.util.apis import arg_utils
import six


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update a Compute Engine virtual machine network interface.

  *{command}* updates network interfaces of a Compute Engine
  virtual machine. For example:

    $ {command} example-instance --zone us-central1-a --aliases r1:172.16.0.1/32

  sets 172.16.0.1/32 from range r1 of the default interface's subnetwork
  as the interface's alias IP.
  """

  support_ipv6_assignment = False

  @classmethod
  def Args(cls, parser):
    instances_flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        '--network-interface',
        default='nic0',
        help='The name of the network interface to update.')
    alias_network_migration_help = ''
    parser.add_argument(
        '--network',
        type=str,
        help='Specifies the network this network interface belongs to.')
    parser.add_argument(
        '--subnetwork',
        type=str,
        help='Specifies the subnetwork this network interface belongs to.')
    parser.add_argument(
        '--private-network-ip',
        dest='private_network_ip',
        type=str,
        help="""\
        Assign the given IP address to the interface. Can be specified only
        together with --network and/or --subnetwork to choose the IP address
        in the new subnetwork. If unspecified, then the previous IP address
        will be allocated in the new subnetwork. If the previous IP address is
        not available in the new subnetwork, then another available IP address
        will be allocated automatically from the new subnetwork CIDR range.
        """)
    alias_network_migration_help = """

        Can be specified together with --network and/or --subnetwork to choose
        IP alias ranges in the new subnetwork. If unspecified, then the previous
        IP alias ranges will be allocated in the new subnetwork. If the previous
        IP alias ranges are not available in the new subnetwork, then other
        available IP alias ranges of the same size will be allocated in the new
        subnetwork."""

    parser.add_argument(
        '--aliases',
        type=str,
        help="""
        The IP alias ranges to allocate for this interface. If there are
        multiple IP alias ranges, they are separated by semicolons.{0}

        For example:

            --aliases="10.128.1.0/24;r1:/32"
        """.format(alias_network_migration_help))

    parser.add_argument(
        '--stack-type',
        choices={
            'IPV4_ONLY':
                'The network interface will be assigned IPv4 addresses.',
            'IPV4_IPV6':
                'The network interface can have both IPv4 and IPv6 addresses.'
        },
        type=arg_utils.ChoiceToEnumName,
        help=('The stack type for the default network interface. Determines if '
              'IPv6 is enabled on the default network interface.'))

    parser.add_argument(
        '--ipv6-network-tier',
        choices={'PREMIUM': ('High quality, Google-grade network tier.')},
        type=arg_utils.ChoiceToEnumName,
        help=('Specifies the IPv6 network tier that will be used to configure '
              'the instance network interface IPv6 access config.'))

    if cls.support_ipv6_assignment:
      parser.add_argument(
          '--ipv6-address',
          type=str,
          help="""
          Assigns the given external IPv6 address to an instance.
          The address must be the first IP in the range. This option can only be
          used on a IPv4 only dual stack instance.
        """)

      parser.add_argument(
          '--ipv6-prefix-length',
          type=int,
          help="""
          Prefix Length of the External IPv6 address range, should be used together
          with --ipv6-address. Currently only /96 is supported and the default value
          is 96.
        """)

      parser.add_argument(
          '--internal-ipv6-address',
          type=str,
          help="""
          Assigns the given internal IPv6 address or range to an instance.
          The address must be the first IP in the range or a IP range with
          /96. This option can only be used on a dual stack instance network
          interface.
        """)

      parser.add_argument(
          '--internal-ipv6-prefix-length',
          type=int,
          help="""
          Optional field that indicates the prefix length of the internal IPv6
          address range, should be used together with
          `--internal-ipv6-address=fd20::`. Currently only /96 is supported and
          the default value is 96. If not set, the prefix length from
          `--internal-ipv6-address=fd20::/96` will be used or assigned a
          default value of 96.
        """)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages
    resources = holder.resources

    instance_ref = instances_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetDefaultScopeLister(holder.client))

    instance = client.instances.Get(
        messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))
    for i in instance.networkInterfaces:
      if i.name == args.network_interface:
        fingerprint = i.fingerprint
        break
    else:
      raise exceptions.UnknownArgumentException(
          'network-interface',
          'Instance does not have a network interface [{}], '
          'present interfaces are [{}].'.format(
              args.network_interface,
              ', '.join([i.name for i in instance.networkInterfaces])))

    network_uri = None
    if getattr(args, 'network', None) is not None:
      network_uri = resources.Parse(
          args.network, {
              'project': instance_ref.project
          },
          collection='compute.networks').SelfLink()

    subnetwork_uri = None
    region = api_utils.ZoneNameToRegionName(instance_ref.zone)
    if getattr(args, 'subnetwork', None) is not None:
      subnetwork_uri = resources.Parse(
          args.subnetwork, {
              'project': instance_ref.project,
              'region': region
          },
          collection='compute.subnetworks').SelfLink()

    stack_type = getattr(args, 'stack_type', None)
    ipv6_address = getattr(args, 'ipv6_address', None)
    ipv6_prefix_length = getattr(args, 'ipv6_prefix_length', None)
    internal_ipv6_address = getattr(args, 'internal_ipv6_address', None)
    internal_ipv6_prefix_length = getattr(args, 'internal_ipv6_prefix_length',
                                          None)
    if stack_type is not None:
      stack_type_enum = (
          messages.NetworkInterface.StackTypeValueValuesEnum(stack_type))
      ipv6_network_tier = getattr(args, 'ipv6_network_tier', None)

      ipv6_access_configs = []
      if ipv6_network_tier is not None:
        # If provide IPv6 network tier then set IPv6 access config in request.
        ipv6_access_config = messages.AccessConfig(
            name=constants.DEFAULT_IPV6_ACCESS_CONFIG_NAME,
            type=messages.AccessConfig.TypeValueValuesEnum.DIRECT_IPV6)
        ipv6_access_config.networkTier = (
            messages.AccessConfig.NetworkTierValueValuesEnum(ipv6_network_tier))
        if ipv6_address:
          # Try interpreting the address as IPv6.
          try:
            # ipaddress only allows unicode input
            ipaddress.ip_address(six.text_type(ipv6_address))
            ipv6_access_config.externalIpv6 = ipv6_address
          except ValueError:
            # ipaddress could not resolve as an IPv6 address.
            ipv6_access_config.externalIpv6 = instances_flags.GetAddressRef(
                resources, ipv6_address, region).SelfLink()
          if ipv6_prefix_length:
            ipv6_access_config.externalIpv6PrefixLength = ipv6_prefix_length
          else:
            ipv6_access_config.externalIpv6PrefixLength = 96
        ipv6_access_configs = [ipv6_access_config]
      if internal_ipv6_address:
        # Try interpreting the address as IPv6.
        try:
          # ipaddress only allows unicode input
          if '/' in six.text_type(internal_ipv6_address):
            ipaddress.ip_network(six.text_type(internal_ipv6_address))
          else:
            ipaddress.ip_address(six.text_type(internal_ipv6_address))
        except ValueError:
          # ipaddress could not resolve as an IPv6 address.
          internal_ipv6_address = instances_flags.GetAddressRef(
              resources, internal_ipv6_address, region).SelfLink()
      patch_network_interface = messages.NetworkInterface(
          aliasIpRanges=(
              alias_ip_range_utils.CreateAliasIpRangeMessagesFromString(
                  messages, True, args.aliases)),
          network=network_uri,
          subnetwork=subnetwork_uri,
          networkIP=getattr(args, 'private_network_ip', None),
          stackType=stack_type_enum,
          ipv6AccessConfigs=ipv6_access_configs,
          fingerprint=fingerprint,
          ipv6Address=internal_ipv6_address,
          internalIpv6PrefixLength=internal_ipv6_prefix_length)
    else:
      patch_network_interface = messages.NetworkInterface(
          aliasIpRanges=(
              alias_ip_range_utils.CreateAliasIpRangeMessagesFromString(
                  messages, True, args.aliases)),
          network=network_uri,
          subnetwork=subnetwork_uri,
          networkIP=getattr(args, 'private_network_ip', None),
          fingerprint=fingerprint)

    request = messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        project=instance_ref.project,
        instance=instance_ref.instance,
        zone=instance_ref.zone,
        networkInterface=args.network_interface,
        networkInterfaceResource=patch_network_interface)

    cleared_fields = []
    if not patch_network_interface.aliasIpRanges:
      cleared_fields.append('aliasIpRanges')
    with client.IncludeFields(cleared_fields):
      operation = client.instances.UpdateNetworkInterface(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')

    operation_poller = poller.Poller(client.instances)
    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Updating network interface [{0}] of instance [{1}]'.format(
            args.network_interface, instance_ref.Name()))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  r"""Update a Compute Engine virtual machine network interface.

  *{command}* updates network interfaces of a Compute Engine
  virtual machine. For example:

    $ {command} example-instance --zone us-central1-a --aliases r1:172.16.0.1/32

  sets 172.16.0.1/32 from range r1 of the default interface's subnetwork
  as the interface's alias IP.
  """

  support_ipv6_assignment = True
