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
"""Command for deleting addresses."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.compute import flags


class Delete(base_classes.BaseAsyncMutator):
  """Release reserved IP addresses."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'names',
        metavar='NAME',
        nargs='+',
        completion_resource='compute.addresses',
        help='The names of the addresses to delete.')

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
    return 'Delete'

  def CreateRequests(self, args):
    """Overrides."""
    self.global_request = getattr(args, 'global')

    if self.global_request:
      return self._CreateGlobalRequests(args)

    return self._CreateRegionalRequests(args)

  def _CreateGlobalRequests(self, args):
    """Create a globally scoped request."""

    # TODO(user): In the future we should support concurrently deleting both
    # region and global addresses
    address_refs = self.CreateGlobalReferences(
        args.names, resource_type='globalAddresses')
    utils.PromptForDeletion(address_refs)
    requests = []
    for address_ref in address_refs:
      request = self.messages.ComputeGlobalAddressesDeleteRequest(
          address=address_ref.Name(),
          project=self.project,
      )
      requests.append(request)

    return requests

  def _CreateRegionalRequests(self, args):
    """Create a regionally scoped request."""

    address_refs = (
        self.CreateRegionalReferences(args.names, args.region))
    utils.PromptForDeletion(address_refs, scope_name='region')
    requests = []
    for address_ref in address_refs:
      request = self.messages.ComputeAddressesDeleteRequest(
          address=address_ref.Name(),
          project=self.project,
          region=address_ref.region,
      )
      requests.append(request)

    return requests


Delete.detailed_help = {
    'brief': 'Release reserved IP addresses',
    'DESCRIPTION': """\
        *{command}* releases one or more Google Compute Engine IP addresses.
        """,
}
