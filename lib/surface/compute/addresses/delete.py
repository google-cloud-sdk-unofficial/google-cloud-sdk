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
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.addresses import flags


class Delete(base_classes.BaseAsyncMutator):
  """Release reserved IP addresses."""

  ADDRESSES_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ADDRESSES_ARG = flags.AddressArgument(required=True)
    cls.ADDRESSES_ARG.AddArgument(parser)

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
    address_refs = self.ADDRESSES_ARG.ResolveAsResource(
        args, self.resources,
        default_scope=compute_scope.ScopeEnum.REGION,
        scope_lister=compute_flags.GetDefaultScopeLister(
            self.compute_client, self.project))

    self.global_request = getattr(address_refs[0], 'region', None) is None

    if self.global_request:
      return self._CreateGlobalRequests(address_refs)

    return self._CreateRegionalRequests(address_refs)

  def _CreateGlobalRequests(self, address_refs):
    """Create a globally scoped request."""

    # TODO(user): In the future we should support concurrently deleting both
    # region and global addresses
    utils.PromptForDeletion(address_refs)
    requests = []
    for address_ref in address_refs:
      request = self.messages.ComputeGlobalAddressesDeleteRequest(
          address=address_ref.Name(),
          project=self.project,
      )
      requests.append(request)

    return requests

  def _CreateRegionalRequests(self, address_refs):
    """Create a regionally scoped request."""

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
