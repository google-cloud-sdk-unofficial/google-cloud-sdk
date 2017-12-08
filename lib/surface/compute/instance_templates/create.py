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
"""Command for creating instance templates."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import instance_template_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags


def _CommonArgs(parser):
  """Common arguments used in Alpha, Beta, and GA."""
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(parser)
  instances_flags.AddLocalSsdArgs(parser)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAddressArgs(parser, instances=False)
  instances_flags.AddMachineTypeArgs(parser)
  instances_flags.AddMaintenancePolicyArgs(parser)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddScopeArgs(parser)
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddImageArgs(parser)
  instances_flags.AddNetworkArgs(parser)

  flags.AddRegionFlag(
      parser,
      resource_type='instance template',
      operation_type='create')

  parser.add_argument(
      '--description',
      help='Specifies a textual description for the instance template.')

  parser.add_argument(
      'name',
      metavar='NAME',
      help='The name of the instance template to create.')


class Create(base_classes.BaseAsyncCreator, image_utils.ImageExpander):
  """Create a Compute Engine virtual machine instance template.

  *{command}* facilitates the creation of Google Compute Engine
  virtual machine instance templates. For example, running:

      $ {command} INSTANCE-TEMPLATE

  will create one instance templates called 'INSTANCE-TEMPLATE'.

  Instance templates are global resources, and can be used to create
  instances in any zone.
  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  @property
  def service(self):
    return self.compute.instanceTemplates

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'instanceTemplates'

  def ValidateDiskFlags(self, args):
    """Validates the values of all disk-related flags."""
    instances_flags.ValidateDiskCommonFlags(args)
    instances_flags.ValidateDiskBootFlags(args)

  def CreateRequests(self, args):
    """Creates and returns an InstanceTemplates.Insert request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      request: a ComputeInstanceTemplatesInsertRequest message object
    """
    self.ValidateDiskFlags(args)
    instances_flags.ValidateLocalSsdFlags(args)

    boot_disk_size_gb = utils.BytesToGb(args.boot_disk_size)
    utils.WarnIfDiskSizeIsTooSmall(boot_disk_size_gb, args.boot_disk_type)

    instance_template_ref = self.CreateGlobalReference(args.name)

    metadata = metadata_utils.ConstructMetadataMessage(
        self.messages,
        metadata=args.metadata,
        metadata_from_file=args.metadata_from_file)

    network_interface = instance_template_utils.CreateNetworkInterfaceMessage(
        scope_prompter=self,
        messages=self.messages,
        network=args.network,
        region=args.region,
        subnet=args.subnet,
        address=(instance_template_utils.EPHEMERAL_ADDRESS
                 if not args.no_address and not args.address
                 else args.address))

    scheduling = instance_utils.CreateSchedulingMessage(
        messages=self.messages,
        maintenance_policy=args.maintenance_policy,
        preemptible=args.preemptible,
        restart_on_failure=args.restart_on_failure)

    service_accounts = instance_utils.CreateServiceAccountMessages(
        messages=self.messages,
        scopes=([] if args.no_scopes else args.scopes))

    create_boot_disk = not instance_utils.UseExistingBootDisk(args.disk or [])
    if create_boot_disk:
      image_uri, _ = self.ExpandImageFlag(
          args,
          return_image_resource=True)
    else:
      image_uri = None

    if args.tags:
      tags = self.messages.Tags(items=args.tags)
    else:
      tags = None

    persistent_disks = (
        instance_template_utils.CreatePersistentAttachedDiskMessages(
            self.messages, args.disk or []))

    if create_boot_disk:
      boot_disk_list = [
          instance_template_utils.CreateDefaultBootAttachedDiskMessage(
              messages=self.messages,
              disk_type=args.boot_disk_type,
              disk_device_name=args.boot_disk_device_name,
              disk_auto_delete=args.boot_disk_auto_delete,
              disk_size_gb=boot_disk_size_gb,
              image_uri=image_uri)]
    else:
      boot_disk_list = []

    local_ssds = [
        instance_utils.CreateLocalSsdMessage(
            self, x.get('device-name'), x.get('interface'))
        for x in args.local_ssd or []]

    disks = boot_disk_list + persistent_disks + local_ssds

    machine_type = instance_utils.InterpretMachineType(
        machine_type=args.machine_type,
        custom_cpu=args.custom_cpu,
        custom_memory=args.custom_memory)

    request = self.messages.ComputeInstanceTemplatesInsertRequest(
        instanceTemplate=self.messages.InstanceTemplate(
            properties=self.messages.InstanceProperties(
                machineType=machine_type,
                disks=disks,
                canIpForward=args.can_ip_forward,
                metadata=metadata,
                networkInterfaces=[network_interface],
                serviceAccounts=service_accounts,
                scheduling=scheduling,
                tags=tags,
            ),
            description=args.description,
            name=instance_template_ref.Name(),
        ),
        project=self.project)

    return [request]
