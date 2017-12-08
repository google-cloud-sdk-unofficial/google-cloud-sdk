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

          $ {command} example-instance --image-family rhel-7 --image-project rhel-cloud --zone us-central1-a
        """,
}


def _CommonArgs(parser, multiple_network_interface_cards,
                release_track):
  """Register parser args common to all tracks."""
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(parser)
  if release_track in [base.ReleaseTrack.ALPHA]:
    instances_flags.AddCreateDiskArgs(parser)
  instances_flags.AddLocalSsdArgs(parser)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAddressArgs(
      parser, instances=True,
      multiple_network_interface_cards=multiple_network_interface_cards)
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

  instances_flags.INSTANCES_ARG.AddArgument(parser)

  csek_utils.AddCsekKeyArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base_classes.BaseAsyncCreator,
             image_utils.ImageExpander,
             zone_utils.ZoneResourceFetcher):
  """Create Google Compute Engine virtual machine instances."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser, multiple_network_interface_cards=False,
                release_track=base.ReleaseTrack.GA)

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
    instances_flags.ValidateAddressFlags(args)

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

    instance_refs = instances_flags.INSTANCES_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))

    # Check if the zone is deprecated or has maintenance coming.
    self.WarnForZonalCreation(instance_refs)

    if hasattr(args, 'network_interface') and args.network_interface:
      network_interfaces = instance_utils.CreateNetworkInterfaceMessages(
          scope_prompter=self,
          compute_client=self.compute_client,
          network_interface_arg=args.network_interface,
          instance_refs=instance_refs)
    else:
      network_interfaces = [
          instance_utils.CreateNetworkInterfaceMessage(
              scope_prompter=self,
              compute_client=self.compute_client,
              network=args.network,
              subnet=args.subnet,
              private_network_ip=args.private_network_ip,
              no_address=args.no_address,
              address=args.address,
              instance_refs=instance_refs)
      ]

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
      image_uri, _ = self.ExpandImageFlag(
          image=args.image,
          image_family=args.image_family,
          image_project=args.image_project,
          return_image_resource=False)
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
      persistent_create_disks = (
          instance_utils.CreatePersistentCreateDiskMessages(
              self,
              self.compute_client,
              self.resources,
              self.csek_keys,
              getattr(args, 'create_disk', []),
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
      disks_messages.append(persistent_disks + persistent_create_disks +
                            local_ssds)

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
              networkInterfaces=network_interfaces,
              serviceAccounts=service_accounts,
              scheduling=scheduling,
              tags=tags,
          ),
          project=self.project,
          zone=instance_ref.zone))

    return requests


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create Google Compute Engine virtual machine instances."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser, multiple_network_interface_cards=False,
                release_track=base.ReleaseTrack.BETA)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create Google Compute Engine virtual machine instances."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser, multiple_network_interface_cards=True,
                release_track=base.ReleaseTrack.ALPHA)


Create.detailed_help = DETAILED_HELP
