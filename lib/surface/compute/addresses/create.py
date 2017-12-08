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

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import name_generator
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags


class Create(base_classes.BaseAsyncMutator):
  """Reserve IP addresses."""

  @staticmethod
  def Args(parser):
    addresses = parser.add_argument(
        '--addresses',
        metavar='ADDRESS',
        type=arg_parsers.ArgList(min_length=1),
        action=arg_parsers.FloatingListValuesCatcher(),
        help='Ephemeral IP addresses to promote to reserved status.')
    addresses.detailed_help = """\
        Ephemeral IP addresses to promote to reserved status. Only addresses
        that are being used by resources in the project can be promoted. When
        providing this flag, a parallel list of names for the addresses can
        be provided. For example,

          $ {command} ADDRESS-1 ADDRESS-2 --addresses 162.222.181.197,162.222.181.198 --region us-central1

        will result in 162.222.181.197 being reserved as
        'ADDRESS-1' and 162.222.181.198 as 'ADDRESS-2'. If
        no names are given, randomly-generated names will be assigned
        to the IP addresses.
        """

    parser.add_argument(
        '--description',
        help='An optional textual description for the addresses.')

    parser.add_argument(
        'names',
        metavar='NAME',
        nargs='*',
        help='The names to assign to the reserved IP addresses.')

    scope = parser.add_mutually_exclusive_group()

    flags.AddRegionFlag(
        scope,
        resource_type='address',
        operation_type='operate on')

    scope.add_argument(
        '--global',
        action='store_true',
        help='If provided, it is assumed the addresses are global.')

  @property
  def service(self):
    if self.global_request:
      return self.compute.globalAddresses
    else:
      return self.compute.addresses

  @property
  def resource_type(self):
    return 'addresses'

  @property
  def method(self):
    return 'Insert'

  def GetNamesAndAddresses(self, args):
    """Returns names and addresses provided in args."""
    if not args.addresses and not args.names:
      raise exceptions.ToolException(
          'At least one name or address must be provided.')

    if args.names:
      names = args.names
    else:
      # If we dont have any names then we must some addresses.
      names = [name_generator.GenerateRandomName() for _ in args.addresses]

    if args.addresses:
      addresses = args.addresses
    else:
      # If we dont have any addresses then we must some names.
      addresses = [None] * len(args.names)

    if len(addresses) != len(names):
      raise exceptions.ToolException(
          'If providing both, you must specify the same number of names as '
          'addresses.')

    return names, addresses

  def CreateRequests(self, args):
    """Overrides."""
    self.global_request = getattr(args, 'global')

    if self.global_request:
      return self._CreateGlobalRequests(args)

    return self._CreateRegionalRequests(args)

  def _CreateGlobalRequests(self, args):
    names, addresses = self.GetNamesAndAddresses(args)
    address_refs = self.CreateGlobalReferences(
        names, resource_type='globalAddresses')

    requests = []
    for address, address_ref in zip(addresses, address_refs):
      request = self.messages.ComputeGlobalAddressesInsertRequest(
          address=self.messages.Address(
              address=address,
              description=args.description,
              name=address_ref.Name(),
          ),
          project=self.project)
      requests.append(request)

    return requests

  def _CreateRegionalRequests(self, args):
    names, addresses = self.GetNamesAndAddresses(args)
    address_refs = self.CreateRegionalReferences(names, args.region)

    requests = []
    for address, address_ref in zip(addresses, address_refs):
      request = self.messages.ComputeAddressesInsertRequest(
          address=self.messages.Address(
              address=address,
              description=args.description,
              name=address_ref.Name(),
          ),
          project=self.project,
          region=address_ref.region)
      requests.append(request)

    return requests


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
