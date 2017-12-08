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

"""Command for deleting access configs from virtual machine instances."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


class DeleteAccessConfig(base_classes.NoOutputAsyncMutator):
  """Delete an access configuration from a virtual machine network interface.

  *{command}* is used to delete access configurations from network
  interfaces of Google Compute Engine virtual machines.
  """

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        '--access-config-name',
        default=constants.DEFAULT_ACCESS_CONFIG_NAME,
        help="""\
        Specifies the name of the access configuration to delete.
        ``{0}'' is used as the default if this flag is not provided.
        """.format(constants.DEFAULT_ACCESS_CONFIG_NAME))
    parser.add_argument(
        '--network-interface',
        default=constants.DEFAULT_NETWORK_INTERFACE,
        action=arg_parsers.StoreOnceAction,
        help="""\
        Specifies the name of the network interface from which to delete the
        access configuration. If this is not provided, then ``nic0'' is used
        as the default.
        """)

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'DeleteAccessConfig'

  @property
  def resource_type(self):
    return 'instances'

  def CreateRequests(self, args):
    """Returns a request necessary for removing an access config."""
    instance_ref = instance_flags.INSTANCE_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))

    request = self.messages.ComputeInstancesDeleteAccessConfigRequest(
        accessConfig=args.access_config_name,
        instance=instance_ref.Name(),
        networkInterface=args.network_interface,
        project=self.project,
        zone=instance_ref.zone)

    return [request]
