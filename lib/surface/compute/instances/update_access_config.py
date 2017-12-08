# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command for updating access configs for virtual machine instances."""
import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAccessConfigInstances(base_classes.ReadWriteCommand):
  """Update a Google Compute Engine virtual machine access configuration.

  *{command}* is used to update access configurations for network
  interfaces of Google Compute Engine virtual machines.
  """

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCE_ARG.AddArgument(parser)
    instance_flags.AddNetworkInterfaceArgs(parser)
    instance_flags.AddPublicDnsArgs(parser, instance=False)

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'UpdateAccessConfig'

  @property
  def resource_type(self):
    return 'instances'

  def CreateReference(self, args):
    instance_flags.ValidatePublicDnsFlags(args)

    return instance_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))

  def GetGetRequest(self, args):
    return (self.service,
            'Get',
            self.messages.ComputeInstancesGetRequest(
                instance=self.ref.Name(),
                project=self.project,
                zone=self.ref.zone))

  def GetSetRequest(self, args, replacement, existing):
    for network_interface in replacement.networkInterfaces:
      if network_interface.name == args.network_interface:
        access_config_replacement = network_interface.accessConfigs[0]

    return (self.service,
            'UpdateAccessConfig',
            self.messages.ComputeInstancesUpdateAccessConfigRequest(
                instance=self.ref.Name(),
                networkInterface=args.network_interface,
                accessConfig=access_config_replacement,
                project=self.project,
                zone=self.ref.zone))

  def Modify(self, args, original):
    if args.public_dns is True:
      set_public_dns = True
    elif args.no_public_dns is True:
      set_public_dns = False
    else:
      set_public_dns = None

    ptr_domain_name = None
    if args.public_ptr is True:
      set_ptr = True
      ptr_domain_name = args.public_ptr_domain
    elif args.no_public_ptr is True:
      set_ptr = False
    else:
      set_ptr = None

    modified = copy.deepcopy(original)
    for interface in modified.networkInterfaces:
      if interface.name == args.network_interface:
        interface.accessConfigs[0].setPublicDns = set_public_dns
        # publicDnsName is output only.
        interface.accessConfigs[0].publicDnsName = None
        interface.accessConfigs[0].setPublicPtr = set_ptr
        interface.accessConfigs[0].publicPtrDomainName = ptr_domain_name

        return modified

    raise exceptions.InvalidArgumentException(
        '--network-interface',
        'The specified network interface \'{0}\' does not exist.'.format(
            args.network_interface))
