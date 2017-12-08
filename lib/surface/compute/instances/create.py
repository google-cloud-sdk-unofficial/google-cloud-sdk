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
import argparse

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import property_selector
from googlecloudsdk.api_lib.compute import resource_specs
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

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
        7'' image available, run:

          $ {command} example-instance --image-family rhel-7 --image-project rhel-cloud --zone us-central1-a
        """,
}


def _CommonArgs(parser, multiple_network_interface_cards, release_track,
                support_alias_ip_ranges, support_public_dns,
                support_network_tier,
                enable_regional=False):
  """Register parser args common to all tracks."""
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(parser, enable_regional)
  if release_track in [base.ReleaseTrack.ALPHA]:
    instances_flags.AddCreateDiskArgs(parser)
    instances_flags.AddExtendedMachineTypeArgs(parser)
  if release_track in [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]:
    instances_flags.AddAcceleratorArgs(parser)
  instances_flags.AddLocalSsdArgs(parser)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAddressArgs(
      parser, instances=True,
      multiple_network_interface_cards=multiple_network_interface_cards,
      support_alias_ip_ranges=support_alias_ip_ranges,
      support_network_tier=support_network_tier)
  instances_flags.AddMachineTypeArgs(parser)
  instances_flags.AddMaintenancePolicyArgs(parser)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddServiceAccountAndScopeArgs(parser, False)
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddPrivateNetworkIpArgs(parser)
  instances_flags.AddImageArgs(parser)
  if support_public_dns:
    instances_flags.AddPublicDnsArgs(parser, instance=True)
  if support_network_tier:
    instances_flags.AddNetworkTierArgs(parser, instance=True)

  parser.add_argument(
      '--description',
      help='Specifies a textual description of the instances.')

  instances_flags.INSTANCES_ARG.AddArgument(parser)

  csek_utils.AddCsekKeyArgs(parser)


# TODO(b/33434068) Refactor away ImageExpander and ZoneResourceFetcher
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create Google Compute Engine virtual machine instances."""

  _support_public_dns = False
  _support_network_tier = False

  def __init__(self, *args, **kwargs):
    super(Create, self).__init__(*args, **kwargs)

    self.__resource_spec = None
    self._compute_holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser, multiple_network_interface_cards=False,
                release_track=base.ReleaseTrack.GA,
                support_alias_ip_ranges=False,
                support_public_dns=cls._support_public_dns,
                support_network_tier=cls._support_network_tier)

  @property
  def resource_type(self):
    return 'instances'

  @property
  def compute_client(self):
    return self._compute_holder.client

  @property
  def messages(self):
    return self.compute_client.messages

  @property
  def compute(self):
    return self.compute_client.apitools_client

  @property
  def project(self):
    return properties.VALUES.core.project.Get(required=True)

  @property
  def resources(self):
    return self._compute_holder.resources

  # absence of any of these properties triggers exception in tests
  @property
  def http(self):
    return self.compute.http

  @property
  def batch_url(self):
    return self.compute_client.batch_url

  @property
  def _resource_spec(self):
    if self.__resource_spec is None:
      # Constructing the spec can be potentially expensive (e.g.,
      # generating the set of valid fields from the protobuf message),
      self.__resource_spec = resource_specs.GetSpec(
          self.resource_type, self.messages, self.compute_client.api_version)
    return self.__resource_spec

  @property
  def transformations(self):
    if self._resource_spec:
      return self._resource_spec.transformations
    else:
      return None

  def Collection(self):
    return 'compute.instances'

  def Format(self, args):
    return self.ListFormat(args)

  def _CreateRequests(self, args):
    instances_flags.ValidateDiskFlags(args)
    instances_flags.ValidateLocalSsdFlags(args)
    instances_flags.ValidateNicFlags(args)
    instances_flags.ValidateServiceAccountAndScopeArgs(args)
    instances_flags.ValidateAcceleratorArgs(args)

    # This feature is only exposed in alpha/beta
    allow_rsa_encrypted = self.ReleaseTrack() in [base.ReleaseTrack.ALPHA,
                                                  base.ReleaseTrack.BETA]
    self.csek_keys = csek_utils.CsekKeyStore.FromArgs(args, allow_rsa_encrypted)

    scheduling = instance_utils.CreateSchedulingMessage(
        messages=self.messages,
        maintenance_policy=args.maintenance_policy,
        preemptible=args.preemptible,
        restart_on_failure=args.restart_on_failure)

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
    zone_resource_fetcher = zone_utils.ZoneResourceFetcher(self.compute_client)
    zone_resource_fetcher.WarnForZonalCreation(instance_refs)

    network_interface_arg = getattr(args, 'network_interface', None)
    if network_interface_arg:
      network_interfaces = instance_utils.CreateNetworkInterfaceMessages(
          resources=self.resources,
          compute_client=self.compute_client,
          network_interface_arg=network_interface_arg,
          instance_refs=instance_refs,
          support_network_tier=self._support_network_tier)
    else:
      if self._support_public_dns is True:
        instances_flags.ValidatePublicDnsFlags(args)

      network_tier = getattr(args, 'network_tier', None)

      network_interfaces = [
          instance_utils.CreateNetworkInterfaceMessage(
              resources=self.resources,
              compute_client=self.compute_client,
              network=args.network,
              subnet=args.subnet,
              private_network_ip=args.private_network_ip,
              no_address=args.no_address,
              address=args.address,
              instance_refs=instance_refs,
              network_tier=network_tier,
              no_public_dns=getattr(args, 'no_public_dns', None),
              public_dns=getattr(args, 'public_dns', None),
              no_public_ptr=getattr(args, 'no_public_ptr', None),
              public_ptr=getattr(args, 'public_ptr', None),
              no_public_ptr_domain=getattr(args, 'no_public_ptr_domain', None),
              public_ptr_domain=getattr(args, 'public_ptr_domain', None))
      ]

    machine_type_uris = instance_utils.CreateMachineTypeUris(
        resources=self.resources,
        compute_client=self.compute_client,
        project=self.project,
        machine_type=args.machine_type,
        custom_cpu=args.custom_cpu,
        custom_memory=args.custom_memory,
        ext=getattr(args, 'custom_extensions', None),
        instance_refs=instance_refs)

    create_boot_disk = not instance_utils.UseExistingBootDisk(args.disk or [])
    if create_boot_disk:
      image_expander = image_utils.ImageExpander(self.compute_client,
                                                 self.resources)
      image_uri, _ = image_expander.ExpandImageFlag(
          user_project=self.project,
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
              self.resources, self.compute_client, self.csek_keys,
              args.disk or [], instance_ref))
      persistent_create_disks = (
          instance_utils.CreatePersistentCreateDiskMessages(
              self,
              self.compute_client,
              self.resources,
              self.csek_keys,
              getattr(args, 'create_disk', []),
              instance_ref))
      local_ssds = []
      for x in args.local_ssd or []:
        local_ssds.append(
            instance_utils.CreateLocalSsdMessage(
                self.resources,
                self.messages,
                x.get('device-name'),
                x.get('interface'),
                instance_ref.zone)
        )

      if create_boot_disk:
        boot_disk = instance_utils.CreateDefaultBootAttachedDiskMessage(
            self.compute_client, self.resources,
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

    accelerator_args = getattr(args, 'accelerator', None)

    project_to_sa = {}
    requests = []
    for instance_ref, machine_type_uri, disks in zip(
        instance_refs, machine_type_uris, disks_messages):
      if instance_ref.project not in project_to_sa:
        scopes = None
        if not args.no_scopes and not args.scopes:
          # User didn't provide any input on scopes. If project has no default
          # service account then we want to create a VM with no scopes
          request = (self.compute.projects,
                     'Get',
                     self.messages.ComputeProjectsGetRequest(
                         project=instance_ref.project))
          errors = []
          result = self.compute_client.MakeRequests([request], errors)
          if not errors:
            if not result[0].defaultServiceAccount:
              scopes = []
              log.status.Print(
                  'There is no default service account for project {}. '
                  'Instance {} will not have scopes.'.format(
                      instance_ref.project, instance_ref.Name))
        if scopes is None:
          scopes = [] if args.no_scopes else args.scopes

        if args.no_service_account:
          service_account = None
        else:
          service_account = args.service_account
        service_accounts = instance_utils.CreateServiceAccountMessages(
            messages=self.messages,
            scopes=scopes,
            service_account=service_account)
        project_to_sa[instance_ref.project] = service_accounts

      instance = self.messages.Instance(
          canIpForward=args.can_ip_forward,
          disks=disks,
          description=args.description,
          machineType=machine_type_uri,
          metadata=metadata,
          name=instance_ref.Name(),
          networkInterfaces=network_interfaces,
          serviceAccounts=project_to_sa[instance_ref.project],
          scheduling=scheduling,
          tags=tags)
      if getattr(args, 'min_cpu_platform', None):
        instance.minCpuPlatform = args.min_cpu_platform
      if accelerator_args:
        accelerator_type_name = accelerator_args['type']
        accelerator_type_ref = self.resources.Parse(
            accelerator_type_name,
            collection='compute.acceleratorTypes',
            params={'project': instance_ref.project,
                    'zone': instance_ref.zone})
        # Accelerator count is default to 1.
        accelerator_count = int(accelerator_args.get('count', 1))
        accelerators = instance_utils.CreateAcceleratorConfigMessages(
            self.compute_client.messages, accelerator_type_ref,
            accelerator_count)
        instance.guestAccelerators = accelerators

      request = self.messages.ComputeInstancesInsertRequest(
          instance=instance,
          project=instance_ref.project,
          zone=instance_ref.zone)

      sole_tenancy_host_arg = getattr(args, 'sole_tenancy_host', None)
      if sole_tenancy_host_arg:
        sole_tenancy_host_ref = self.resources.Parse(
            sole_tenancy_host_arg, collection='compute.hosts',
            params={'zone': instance_ref.zone})
        request.instance.host = sole_tenancy_host_ref.SelfLink()
      requests.append((self.compute.instances, 'Insert', request))
    return requests

  def Run(self, args):
    errors = []
    requests = self._CreateRequests(args)
    resource_list = self.compute_client.MakeRequests(requests, errors)

    # changes machine type uri to just machine type name
    resource_list = lister.ProcessResults(
        resources=resource_list,
        field_selector=property_selector.PropertySelector(
            properties=None,
            transformations=self.transformations))

    if errors:
      utils.RaiseToolException(errors)

    return resource_list


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create Google Compute Engine virtual machine instances."""

  _support_public_dns = False
  _support_network_tier = False

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        multiple_network_interface_cards=True,
        release_track=base.ReleaseTrack.BETA,
        support_alias_ip_ranges=False,
        support_public_dns=cls._support_public_dns,
        support_network_tier=cls._support_network_tier)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create Google Compute Engine virtual machine instances."""

  _support_public_dns = True
  _support_network_tier = True

  @classmethod
  def Args(cls, parser):
    parser.add_argument('--sole-tenancy-host', help=argparse.SUPPRESS)
    _CommonArgs(parser, multiple_network_interface_cards=True,
                release_track=base.ReleaseTrack.ALPHA,
                support_alias_ip_ranges=True,
                support_public_dns=cls._support_public_dns,
                support_network_tier=cls._support_network_tier,
                enable_regional=True)
    instances_flags.AddMinCpuPlatformArgs(parser)


Create.detailed_help = DETAILED_HELP
