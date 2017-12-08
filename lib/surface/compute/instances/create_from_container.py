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
"""Command for creating VM instances running Docker images."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateFromContainer(base_classes.BaseAsyncCreator,
                          zone_utils.ZoneResourceFetcher):
  """Command for creating VM instances running Docker images."""

  @staticmethod
  def Args(parser):
    """Register parser args."""
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
    instances_flags.AddDockerArgs(parser)
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
    instances_flags.ValidateDockerArgs(args)
    instances_flags.ValidateDiskCommonFlags(args)
    instances_flags.ValidateLocalSsdFlags(args)
    if instance_utils.UseExistingBootDisk(args.disk or []):
      raise exceptions.InvalidArgumentException(
          '--disk',
          'Boot disk specified for containerized VM.')

    scheduling = instance_utils.CreateSchedulingMessage(
        messages=self.messages,
        maintenance_policy=args.maintenance_policy,
        preemptible=args.preemptible,
        restart_on_failure=args.restart_on_failure)

    service_accounts = instance_utils.CreateServiceAccountMessages(
        messages=self.messages,
        scopes=([] if args.no_scopes else args.scopes))

    user_metadata = metadata_utils.ConstructMetadataMessage(
        self.messages,
        metadata=args.metadata,
        metadata_from_file=args.metadata_from_file)
    containers_utils.ValidateUserMetadata(user_metadata)

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

    image_uri = containers_utils.ExpandGciImageFlag(self.compute_client)
    requests = []
    for instance_ref, machine_type_uri in zip(instance_refs, machine_type_uris):
      metadata = containers_utils.CreateMetadataMessage(
          self.messages, args.run_as_privileged, args.container_manifest,
          args.docker_image, args.port_mappings, args.run_command,
          user_metadata, instance_ref.Name())
      requests.append(self.messages.ComputeInstancesInsertRequest(
          instance=self.messages.Instance(
              canIpForward=args.can_ip_forward,
              disks=(self._CreateDiskMessages(args, boot_disk_size_gb,
                                              image_uri, instance_ref)),
              description=args.description,
              machineType=machine_type_uri,
              metadata=metadata,
              name=instance_ref.Name(),
              networkInterfaces=[network_interface],
              serviceAccounts=service_accounts,
              scheduling=scheduling,
              tags=containers_utils.CreateTagsMessage(self.messages, args.tags),
          ),
          project=self.project,
          zone=instance_ref.zone))
    return requests

  def _CreateDiskMessages(
      self, args, boot_disk_size_gb, image_uri, instance_ref):
    """Creates API messages with disks attached to VM instance."""
    persistent_disks, _ = (
        instance_utils.CreatePersistentAttachedDiskMessages(
            self, self.compute_client, None, args.disk or [],
            instance_ref))
    local_ssds = [
        instance_utils.CreateLocalSsdMessage(
            self, x.get('device-name'), x.get('interface'), instance_ref.zone)
        for x in args.local_ssd or []]
    boot_disk = instance_utils.CreateDefaultBootAttachedDiskMessage(
        self, self.compute_client, self.resources,
        disk_type=args.boot_disk_type,
        disk_device_name=args.boot_disk_device_name,
        disk_auto_delete=args.boot_disk_auto_delete,
        disk_size_gb=boot_disk_size_gb,
        require_csek_key_create=None,
        image_uri=image_uri,
        instance_ref=instance_ref,
        csek_keys=None)
    return [boot_disk] + persistent_disks + local_ssds


CreateFromContainer.detailed_help = {
    'brief': """\
    Command for creating Google Compute engine virtual machine instances running Docker images.
    """,
    'DESCRIPTION': """\
        *{command}* facilitates the creation of Google Compute Engine virtual
        machines that runs a Docker image. For example, running:

          $ {command} instance-1 --zone us-central1-a --docker-image=gcr.io/google-containers/busybox

        will create an instance called instance-1, in the us-central1-a zone,
        running the 'busybox' image.

        For more examples, refer to the *EXAMPLES* section below.
        """,
    'EXAMPLES': """\
        To run the gcr.io/google-containers/busybox image on an instance named
        'instance-1' that exposes port 80, run:

          $ {command} instance-1 --docker-image=gcr.io/google-containers/busybox --port-mappings=80:80:TCP

        To run the gcr.io/google-containers/busybox image on an instance named
        'instance-1' that executes 'echo "Hello world"' as a run command, run:

          $ {command} instance-1 --docker-image=gcr.io/google-containers/busybox --run-command='echo "Hello world"'

        To run the gcr.io/google-containers/busybox image in privileged mode, run:

          $ {command} instance-1 --docker-image=gcr.io/google-containers/busybox --run-as-privileged

        To run a Docker deployment described by a container manifest in a
        containers.json file, run:

          $ {command} instance-1 --container-manifest=containers.json
        """
}
