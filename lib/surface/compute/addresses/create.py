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
"""Command for reserving IP addresses."""

from googlecloudsdk.api_lib.compute import addresses_utils as utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.addresses import flags


def _Args(cls, parser):
  """Argument parsing."""

  cls.ADDRESSES_ARG = flags.AddressArgument(required=False)
  cls.ADDRESSES_ARG.AddArgument(parser)
  flags.AddDescription(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Create(utils.AddressesMutator):
  """Reserve IP addresses."""

  ADDRESSES_ARG = None

  @classmethod
  def Args(cls, parser):
    _Args(cls, parser)
    flags.AddAddresses(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Reserve IP addresses."""

  @classmethod
  def Args(cls, parser):
    _Args(cls, parser)
    flags.AddAddressesAndIPVersions(parser, required=False)

    parser.add_argument(
        '--network-tier',
        choices=['PREMIUM', 'SELECT'],
        type=lambda x: x.upper(),
        help='The network tier to assign to the reserved IP addresses. If left '
        'empty, `PREMIUM` is used. Supported network tiers are: `PREMIUM`, '
        '`SELECT`.')

  def ConstructNetworkTier(self, args):
    if args.network_tier:
      return self.messages.Address.NetworkTierValueValuesEnum(args.network_tier)
    else:
      return None

  def GetAddress(self, args, address, address_ref):
    """Override."""
    network_tier = self.ConstructNetworkTier(args)

    if args.ip_version or (address is None and self.global_request):
      ip_version = self.messages.Address.IpVersionValueValuesEnum(
          args.ip_version or 'IPV4')
    else:
      # IP version is only specified in global requests if an address is not
      # specified to determine whether an ipv4 or ipv6 address should be
      # allocated.
      ip_version = None

    return self.messages.Address(
        address=address,
        description=args.description,
        networkTier=network_tier,
        ipVersion=ip_version,
        name=address_ref.Name())


Create.detailed_help = {
    'brief': 'Reserve IP addresses',
    'DESCRIPTION': """\
        *{command}* is used to reserve one or more IP addresses. Once
        an IP address is reserved, it will be associated with the
        project until it is released using 'gcloud compute addresses
        delete'. Ephemeral IP addresses that are in use by resources
        in the project, can be reserved using the ``--addresses''
        flag.
        """,
    'EXAMPLES': """\
        To reserve three IP addresses in the ``us-central1'' region,
        run:

          $ {command} ADDRESS-1 ADDRESS-2 ADDRESS-3 --region us-central1

        To reserve ephemeral IP addresses 162.222.181.198 and
        23.251.146.189 which are being used by virtual machine
        instances in the ``us-central1'' region, run:

          $ {command} --addresses 162.222.181.198,23.251.146.189 --region us-central1

        In the above invocation, the two addresses will be assigned
        random names.
        """,
}

CreateAlpha.detailed_help = Create.detailed_help
