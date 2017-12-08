# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Command for removing an interface from a router."""

import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.core import exceptions


class InterfaceNotFoundError(exceptions.Error):
  """Raised when an interface is not found."""

  def __init__(self, name):
    self.name = name
    msg = 'interface `{0}` not found'.format(name)
    super(InterfaceNotFoundError, self
         ).__init__(msg)


class RemoveBgpPeer(base_classes.ReadWriteCommand):
  """Remove an interface from a router."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='update')

    parser.add_argument(
        '--interface-name',
        required=True,
        help='The name of the interface being removed.')

  @property
  def service(self):
    return self.compute.routers

  @property
  def resource_type(self):
    return 'routers'

  def CreateReference(self, args):
    return self.ROUTER_ARG.ResolveAsResource(args, self.resources)

  def GetGetRequest(self, args):
    return (self.service,
            'Get',
            self.messages.ComputeRoutersGetRequest(
                router=self.ref.Name(),
                region=self.ref.region,
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    return (self.service,
            'Update',
            self.messages.ComputeRoutersUpdateRequest(
                router=self.ref.Name(),
                routerResource=replacement,
                region=self.ref.region,
                project=self.project))

  def Modify(self, args, existing):
    replacement = copy.deepcopy(existing)

    # remove interface if exists
    interface = None
    for i in replacement.interfaces:
      if i.name == args.interface_name:
        interface = i
        replacement.interfaces.remove(interface)
        break

    if interface is None:
      raise InterfaceNotFoundError(args.interface_name)

    return replacement


RemoveBgpPeer.detailed_help = {
    'DESCRIPTION': """
        *{command}* removes an interface from a router.
        """,
}
