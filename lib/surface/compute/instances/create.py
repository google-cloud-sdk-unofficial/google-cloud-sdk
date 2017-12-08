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
"""Command for creating instances."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags

DETAILED_HELP = {
    'DESCRIPTION': """\
        *{command}* facilitates the creation of Google Compute Engine
        virtual machines. For example, running:

          $ {command} example-instance-1 example-instance-2 example-instance-3 --zone us-central1-a

        will create three instances called `example-instance-1`,
        `example-instance-2`, and `example-instance-3` in the
        `us-central1-a` zone.

        When an instance is in RUNNING state and the system begins to boot,
        the instance creation is considered finished, and the command returns
        with a list of new virtual machines.  Note that you usually cannot log
        into a new instance until it finishes booting. Check the progress of an
        instance using `gcloud compute instances get-serial-port-output`.

        For more examples, refer to the *EXAMPLES* section below.
        """,
    'EXAMPLES': """\
        To create an instance with the latest ``Red Hat Enterprise Linux
        6'' image available, run:

          $ {command} example-instance --image rhel-6 --zone us-central1-a
        """,
}


def _CommonArgs(parser):
  """Register parser args common to all tracks."""
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(parser)
  instances_flags.AddLocalSsdArgs(parser)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAddressArgs(parser, instances=True)
  instances_flags.AddMachineTypeArgs(parser)
  instances_flags.AddMaintenancePolicyArgs(parser)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddScopeArgs(parser)
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddPrivateNetworkIpArgs(parser)
  instances_flags.AddImageArgs(parser)

  parser.add_argument(
      '--description',
      help='Specifies a textual description of the instances.')

  parser.add_argument(
      'names',
      metavar='NAME',
      nargs='+',
      help='The names of the instances to create.')

  flags.AddZoneFlag(
      parser,
      resource_type='instances',
      operation_type='create')

  csek_utils.AddCsekKeyArgs(parser)


class Create(base_classes.BaseAsyncCreator,
             image_utils.ImageExpander,
             zone_utils.ZoneResourceFetcher):
  """Create Google Compute Engine virtual machine instances."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'instances'

  def CreateRequests(self, args):
    instances_flags.ValidateDiskFlags(args)
    instances_flags.ValidateLocalSsdFlags(args)

    # This feature is only exposed in alpha/beta
    allow_rsa_encrypted = self.ReleaseTrack() in [base.ReleaseTrack.ALPHA,
                                                  base.ReleaseTrack.BETA]
    self.csek_keys = csek_utils.CsekKeyStore.FromArgs(args, allow_rsa_encrypted)

    scheduling = instance_utils.CreateSchedulingMessage(
        messages=self.messages,
        maintenance_policy=args.maintenance_policy,
        preemptible=args.preemptible,
        restart_on_failure=args.restart_on_failure)

    service_accounts = instance_utils.CreateServiceAccountMessages(
        messages=self.messages,
        scopes=([] if args.no_scopes else args.scopes))

    if args.tags:
      tags = self.messages.Tags(items=args.tags)
    else:
      tags = None

    metadata = metadata_utils.ConstructMetadataMessage(
        self.messages,
        metadata=args.metadata,
        metadata_from_file=args.metadata_from_file)

    # If the user already provided an initial Windows password and
    # username through metadata, then there is no need to check
    # whether the image or the boot disk is Windows.

    boot_disk_size_gb = utils.BytesToGb(args.boot_disk_size)
    utils.WarnIfDiskSizeIsTooSmall(boot_disk_size_gb, args.boot_disk_type)

    instance_refs = self.CreateZonalReferences(args.names, args.zone)

    # Check if the zone is deprecated or has maintenance coming.
    self.WarnForZonalCreation(instance_refs)

    network_interface = instance_utils.CreateNetworkInterfaceMessage(
        scope_prompter=self,
        compute_client=self.compute_client,
        network=args.network,
        subnet=args.subnet,
        private_network_ip=args.private_network_ip,
        no_address=args.no_address,
        address=args.address,
        instance_refs=instance_refs)

    machine_type_uris = instance_utils.CreateMachineTypeUris(
        scope_prompter=self,
        compute_client=self.compute_client,
        project=self.project,
        machine_type=args.machine_type,
        custom_cpu=args.custom_cpu,
        custom_memory=args.custom_memory,
        instance_refs=instance_refs)

    create_boot_disk = not instance_utils.UseExistingBootDisk(args.disk or [])
    if create_boot_disk:
      image_uri, _ = self.ExpandImageFlag(args, return_image_resource=False)
    else:
      image_uri = None

    # A list of lists where the element at index i contains a list of
    # disk messages that should be set for the instance at index i.
    disks_messages = []

    # A mapping of zone to boot disk references for all existing boot
    # disks that are being attached.
    # TODO(user): Simplify this once resources.Resource becomes
    # hashable.
    existing_boot_disks = {}

    for instance_ref in instance_refs:
      persistent_disks, boot_disk_ref = (
          instance_utils.CreatePersistentAttachedDiskMessages(
              self, self.compute_client, self.csek_keys, args.disk or [],
              instance_ref))
      local_ssds = [
          instance_utils.CreateLocalSsdMessage(
              self, x.get('device-name'), x.get('interface'), instance_ref.zone)
          for x in args.local_ssd or []]
      if create_boot_disk:
        boot_disk = instance_utils.CreateDefaultBootAttachedDiskMessage(
            self, self.compute_client, self.resources,
            disk_type=args.boot_disk_type,
            disk_device_name=args.boot_disk_device_name,
            disk_auto_delete=args.boot_disk_auto_delete,
            disk_size_gb=boot_disk_size_gb,
            require_csek_key_create=(
                args.require_csek_key_create if self.csek_keys else None),
            image_uri=image_uri,
            instance_ref=instance_ref,
            csek_keys=self.csek_keys)
        persistent_disks = [boot_disk] + persistent_disks
      else:
        existing_boot_disks[boot_disk_ref.zone] = boot_disk_ref
      disks_messages.append(persistent_disks + local_ssds)

    requests = []
    for instance_ref, machine_type_uri, disks in zip(
        instance_refs, machine_type_uris, disks_messages):
      requests.append(self.messages.ComputeInstancesInsertRequest(
          instance=self.messages.Instance(
              canIpForward=args.can_ip_forward,
              disks=disks,
              description=args.description,
              machineType=machine_type_uri,
              metadata=metadata,
              name=instance_ref.Name(),
              networkInterfaces=[network_interface],
              serviceAccounts=service_accounts,
              scheduling=scheduling,
              tags=tags,
          ),
          project=self.project,
          zone=instance_ref.zone))

    return requests


Create.detailed_help = DETAILED_HELP
