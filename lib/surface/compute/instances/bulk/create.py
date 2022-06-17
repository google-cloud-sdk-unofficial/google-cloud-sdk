# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import filter_rewrite
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute.instances.create import utils as create_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import resource_manager_tags_utils
from googlecloudsdk.command_lib.compute import scope as compute_scopes
from googlecloudsdk.command_lib.compute import secure_tags_utils
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags as maintenance_flags
from googlecloudsdk.command_lib.compute.resource_policies import util as maintenance_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
import six

DETAILED_HELP = {
    'brief':
        """
          Create multiple Compute Engine virtual machines.
        """,
    'DESCRIPTION':
        """
        *{command}* facilitates the creation of multiple Compute Engine
        virtual machines with a single command. They offer a number of advantages
        compared to the single instance creation command. This includes the
        ability to automatically pick a zone in which to create instances based
        on resource availability, the ability to specify that the request be
        atomic or best-effort, and a faster rate of instance creation.
        """,
    'EXAMPLES':
        """
        To create instances called 'example-instance-1', 'example-instance-2',
        and 'example-instance-3' in the 'us-central1-a' zone, run:

          $ {command} --predefined-names=example-instance-1,example-instance-2,example-instance-3 --zone=us-central1-a
        """,
}


def _CommonArgs(parser,
                deprecate_maintenance_policy=False,
                support_min_node_cpu=False,
                support_erase_vss=False,
                snapshot_csek=False,
                image_csek=False,
                support_display_device=False,
                support_local_ssd_size=False,
                support_numa_node_count=False,
                support_visible_core_count=False,
                support_max_run_duration=False,
                support_enable_target_shape=False):
  """Register parser args common to all tracks."""
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgsForBulk(parser)
  instances_flags.AddCreateDiskArgs(
      parser,
      enable_kms=True,
      enable_snapshots=True,
      source_snapshot_csek=snapshot_csek,
      image_csek=image_csek,
      include_name=False,
      support_boot=True)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAcceleratorArgs(parser)
  instances_flags.AddMachineTypeArgs(parser)
  instances_flags.AddMaintenancePolicyArgs(
      parser, deprecate=deprecate_maintenance_policy)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddProvisioningModelVmArgs(parser)
  instances_flags.AddNetworkPerformanceConfigsArgs(parser)
  instances_flags.AddInstanceTerminationActionVmArgs(parser)
  instances_flags.AddServiceAccountAndScopeArgs(
      parser,
      False,
      extra_scopes_help='However, if neither `--scopes` nor `--no-scopes` are '
      'specified and the project has no default service '
      'account, then the instance will be created with no '
      'scopes. Note that the level of access that a service '
      'account has is determined by a combination of access '
      'scopes and IAM roles so you must configure both '
      'access scopes and IAM roles for the service account '
      'to work properly.')
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddNoAddressArg(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddNetworkTierArgs(parser, instance=True)
  instances_flags.AddBulkCreateNetworkingArgs(parser)

  instances_flags.AddImageArgs(parser, enable_snapshots=True)
  instances_flags.AddShieldedInstanceConfigArgs(parser)
  instances_flags.AddNestedVirtualizationArgs(parser)
  instances_flags.AddThreadsPerCoreArgs(parser)
  instances_flags.AddEnableUefiNetworkingArgs(parser)
  instances_flags.AddResourceManagerTagsArgs(parser)
  if support_numa_node_count:
    instances_flags.AddNumaNodeCountArgs(parser)

  if support_display_device:
    instances_flags.AddDisplayDeviceArg(parser)

  instances_flags.AddReservationAffinityGroup(
      parser,
      group_text='Specifies the reservation for the instance.',
      affinity_text='The type of reservation for the instance.')

  maintenance_flags.AddResourcePoliciesArgs(parser, 'added to', 'instance')

  if support_min_node_cpu:
    instances_flags.AddMinNodeCpuArg(parser)

  instances_flags.AddLocationHintArg(parser)

  if support_erase_vss:
    flags.AddEraseVssSignature(parser, 'source snapshots or source machine'
                               ' image')

  labels_util.AddCreateLabelsFlags(parser)

  parser.add_argument(
      '--description', help='Specifies a textual description of the instances.')

  base.ASYNC_FLAG.AddToParser(parser)
  parser.display_info.AddFormat(
      'multi(instances:format="table(name,zone.basename())")')

  if support_visible_core_count:
    instances_flags.AddVisibleCoreCountArgs(parser)

  if support_local_ssd_size:
    instances_flags.AddLocalSsdArgsWithSize(parser)
  else:
    instances_flags.AddLocalSsdArgs(parser)

  if support_max_run_duration:
    instances_flags.AddMaxRunDurationVmArgs(parser)

  if support_enable_target_shape:
    instances_flags.AddDistributionTargetShapeArgs(parser)


def _GetOperations(compute_client, project, operation_group_id):
  """Requests operations with group id matching the given one."""

  errors_to_collect = []

  _, operation_filter = filter_rewrite.Rewriter().Rewrite(
      expression='operationGroupId=' + operation_group_id)

  operations_response = compute_client.MakeRequests(
      [(compute_client.apitools_client.globalOperations, 'AggregatedList',
        compute_client.apitools_client.globalOperations.GetRequestType(
            'AggregatedList')(filter=operation_filter, project=project))],
      errors_to_collect=errors_to_collect,
      log_result=False,
      always_return_operation=True,
      no_followup=True)

  return operations_response, errors_to_collect


def _GetResult(compute_client, request, operation_group_id):
  """Requests operations with group id and parses them as an output."""

  operations_response, errors = _GetOperations(compute_client, request.project,
                                               operation_group_id)
  result = {'operationGroupId': operation_group_id, 'instances': []}
  if not errors:
    successful = [
        op for op in operations_response if op.operationType == 'insert' and
        str(op.status) == 'DONE' and op.error is None
    ]
    num_successful = len(successful)
    num_unsuccessful = request.bulkInsertInstanceResource.count - num_successful

    def GetInstanceStatus(op):
      return {
          'id': op.targetId,
          'name': op.targetLink.split('/')[-1],
          'zone': op.zone,
          'selfLink': op.targetLink
      }

    instances_status = [GetInstanceStatus(op) for op in successful]

    result['createdInstanceCount'] = num_successful
    result['failedInstanceCount'] = num_unsuccessful
    result['instances'] = instances_status

  return result


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Create Compute Engine virtual machine instances."""

  _support_nvdimm = False
  _support_public_dns = False
  _support_erase_vss = True
  _support_min_node_cpu = True
  _support_source_snapshot_csek = False
  _support_image_csek = True
  _support_confidential_compute = True
  _support_post_key_revocation_action_type = True
  _support_rsa_encrypted = True
  _deprecate_maintenance_policy = True
  _support_create_disk_snapshots = True
  _support_boot_snapshot_uri = True
  _support_display_device = False
  _support_local_ssd_size = False
  _support_secure_tags = False
  _support_host_error_timeout_seconds = False
  _support_numa_node_count = False
  _support_visible_core_count = False
  _support_max_run_duration = False
  _support_enable_target_shape = False

  _log_async = False

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        deprecate_maintenance_policy=cls._deprecate_maintenance_policy,
        support_min_node_cpu=cls._support_min_node_cpu,
        support_erase_vss=cls._support_erase_vss,
        snapshot_csek=cls._support_source_snapshot_csek,
        image_csek=cls._support_image_csek,
        support_display_device=cls._support_display_device,
        support_local_ssd_size=cls._support_local_ssd_size,
        support_numa_node_count=cls._support_numa_node_count,
        support_visible_core_count=cls._support_visible_core_count,
        support_max_run_duration=cls._support_max_run_duration,
        support_enable_target_shape=cls._support_enable_target_shape)
    cls.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeBulkSourceInstanceTemplateArg())
    cls.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.GA)
    instances_flags.AddPublicDnsArgs(parser, instance=True)
    instances_flags.AddConfidentialComputeArgs(parser)
    instances_flags.AddPostKeyRevocationActionTypeArgs(parser)
    instances_flags.AddBulkCreateArgs(parser)

  def Collection(self):
    return 'compute.instances'

  def GetSourceInstanceTemplate(self, args, resources):
    """Get sourceInstanceTemplate value as required by API."""
    if not args.IsSpecified('source_instance_template'):
      return None
    ref = self.SOURCE_INSTANCE_TEMPLATE.ResolveAsResource(args, resources)
    return ref.SelfLink()

  def GetLocationPolicy(self, args, messages):
    if not args.IsSpecified('location_policy') and (
        not self._support_enable_target_shape or
        not args.IsSpecified('target_distribution_shape')):
      return None

    location_policy = messages.LocationPolicy()
    if args.IsSpecified('location_policy'):
      location_policy.locations = self.GetLocationPolicyLocations(
          args, messages)

    if (self._support_enable_target_shape and
        args.IsSpecified('target_distribution_shape')):
      location_policy.targetShape = arg_utils.ChoiceToEnum(
          args.target_distribution_shape,
          messages.LocationPolicy.TargetShapeValueValuesEnum)

    return location_policy

  def GetLocationPolicyLocations(self, args, messages):
    locations = []
    for zone, policy in args.location_policy.items():
      zone_policy = arg_utils.ChoiceToEnum(
          policy, messages.LocationPolicyLocation.PreferenceValueValuesEnum)
      locations.append(
          messages.LocationPolicy.LocationsValue.AdditionalProperty(
              key='zones/{}'.format(zone),
              value=messages.LocationPolicyLocation(preference=zone_policy)))
    return messages.LocationPolicy.LocationsValue(
        additionalProperties=locations)

  def _CreateRequests(self, args, holder, compute_client, resource_parser,
                      project, location, scope):
    # gcloud creates default values for some fields in Instance resource
    # when no value was specified on command line.
    # When --source-instance-template was specified, defaults are taken from
    # Instance Template and gcloud flags are used to override them - by default
    # fields should not be initialized.

    name_pattern = args.name_pattern
    instance_names = args.predefined_names or []
    instance_count = args.count or len(instance_names)
    per_instance_props = encoding.DictToAdditionalPropertyMessage(
        {el: {} for el in instance_names}, compute_client.messages
        .BulkInsertInstanceResource.PerInstancePropertiesValue)

    location_policy = self.GetLocationPolicy(args, compute_client.messages)

    instance_min_count = instance_count
    if args.IsSpecified('min_count'):
      instance_min_count = args.min_count

    source_instance_template = self.GetSourceInstanceTemplate(
        args, resource_parser)
    skip_defaults = source_instance_template is not None

    scheduling = instance_utils.GetScheduling(
        args,
        compute_client,
        skip_defaults,
        support_node_affinity=False,
        support_min_node_cpu=self._support_min_node_cpu,
        support_host_error_timeout_seconds=self
        ._support_host_error_timeout_seconds,
        support_max_run_duration=self._support_max_run_duration)
    tags = instance_utils.GetTags(args, compute_client)
    labels = instance_utils.GetLabels(
        args, compute_client, instance_properties=True)
    metadata = instance_utils.GetMetadata(args, compute_client, skip_defaults)

    network_interfaces = create_utils.GetBulkNetworkInterfaces(
        args=args,
        resource_parser=resource_parser,
        compute_client=compute_client,
        holder=holder,
        project=project,
        location=location,
        scope=scope,
        skip_defaults=skip_defaults)

    create_boot_disk = not (
        instance_utils.UseExistingBootDisk((args.disk or []) +
                                           (args.create_disk or [])))
    image_uri = create_utils.GetImageUri(args, compute_client, create_boot_disk,
                                         project, resource_parser)

    shielded_instance_config = create_utils.BuildShieldedInstanceConfigMessage(
        messages=compute_client.messages, args=args)

    confidential_vm = False
    if self._support_confidential_compute:
      confidential_instance_config = (
          create_utils.BuildConfidentialInstanceConfigMessage(
              messages=compute_client.messages, args=args))

      confidential_vm = (
          args.IsSpecified('confidential_compute') and
          args.confidential_compute)

    service_accounts = create_utils.GetProjectServiceAccount(
        args, project, compute_client, skip_defaults)

    boot_disk_size_gb = instance_utils.GetBootDiskSizeGb(args)

    disks = []
    if create_utils.CheckSpecifiedDiskArgs(
        args=args, support_disks=False, skip_defaults=skip_defaults):

      #  Disks in bulk insert should be in READ_ONLY mode
      for disk in args.disk or []:
        disk['mode'] = 'ro'
      disks = create_utils.CreateDiskMessages(
          args=args,
          project=project,
          location=location,
          scope=scope,
          compute_client=compute_client,
          resource_parser=resource_parser,
          image_uri=image_uri,
          create_boot_disk=create_boot_disk,
          boot_disk_size_gb=boot_disk_size_gb,
          support_kms=True,
          support_nvdimm=self._support_nvdimm,
          support_source_snapshot_csek=self._support_source_snapshot_csek,
          support_boot_snapshot_uri=self._support_boot_snapshot_uri,
          support_image_csek=self._support_image_csek,
          support_create_disk_snapshots=self._support_create_disk_snapshots,
          use_disk_type_uri=False)

    machine_type_name = None
    if instance_utils.CheckSpecifiedMachineTypeArgs(args, skip_defaults):
      machine_type_name = instance_utils.CreateMachineTypeName(
          args, confidential_vm)

      # Check to see if the custom machine type ratio is supported
      instance_utils.CheckCustomCpuRamRatio(compute_client, project, location,
                                            machine_type_name)

    can_ip_forward = instance_utils.GetCanIpForward(args, skip_defaults)
    guest_accelerators = create_utils.GetAcceleratorsForInstanceProperties(
        args=args, compute_client=compute_client)

    # Create an AdvancedMachineFeatures message if any arguments are supplied
    # that require one.
    advanced_machine_features = None
    if (args.enable_nested_virtualization is not None or
        args.threads_per_core is not None or
        (self._support_numa_node_count and args.numa_node_count is not None) or
        (self._support_visible_core_count and
         args.visible_core_count is not None) or
        args.enable_uefi_networking is not None):
      visible_core_count = args.visible_core_count if self._support_visible_core_count else None
      advanced_machine_features = (
          instance_utils.CreateAdvancedMachineFeaturesMessage(
              compute_client.messages, args.enable_nested_virtualization,
              args.threads_per_core,
              args.numa_node_count if self._support_numa_node_count else None,
              visible_core_count, args.enable_uefi_networking))

    parsed_resource_policies = []
    resource_policies = getattr(args, 'resource_policies', None)
    if resource_policies:
      for policy in resource_policies:
        resource_policy_ref = maintenance_util.ParseResourcePolicyWithScope(
            resource_parser,
            policy,
            project=project,
            location=location,
            scope=scope)
        parsed_resource_policies.append(resource_policy_ref.Name())

    display_device = None
    if self._support_display_device and args.IsSpecified(
        'enable_display_device'):
      display_device = compute_client.messages.DisplayDevice(
          enableDisplay=args.enable_display_device)

    reservation_affinity = instance_utils.GetReservationAffinity(
        args, compute_client)

    instance_properties = compute_client.messages.InstanceProperties(
        canIpForward=can_ip_forward,
        description=args.description,
        disks=disks,
        guestAccelerators=guest_accelerators,
        labels=labels,
        machineType=machine_type_name,
        metadata=metadata,
        minCpuPlatform=args.min_cpu_platform,
        networkInterfaces=network_interfaces,
        serviceAccounts=service_accounts,
        scheduling=scheduling,
        tags=tags,
        resourcePolicies=parsed_resource_policies,
        shieldedInstanceConfig=shielded_instance_config,
        reservationAffinity=reservation_affinity,
        advancedMachineFeatures=advanced_machine_features)

    if self._support_secure_tags and args.secure_tags:
      instance_properties.secureTags = secure_tags_utils.GetSecureTags(
          args.secure_tags)
    if args.resource_manager_tags:
      ret_resource_manager_tags = resource_manager_tags_utils.GetResourceManagerTags(
          args.resource_manager_tags)
      if ret_resource_manager_tags is not None:
        properties_message = compute_client.messages.InstanceProperties
        instance_properties.resourceManagerTags = properties_message.ResourceManagerTagsValue(
            additionalProperties=[
                properties_message.ResourceManagerTagsValue.AdditionalProperty(
                    key=key, value=value) for key, value in sorted(
                        six.iteritems(ret_resource_manager_tags))
            ])

    if self._support_display_device and display_device:
      instance_properties.displayDevice = display_device

    if self._support_confidential_compute and confidential_instance_config:
      instance_properties.confidentialInstanceConfig = confidential_instance_config

    if self._support_erase_vss and args.IsSpecified(
        'erase_windows_vss_signature'):
      instance_properties.eraseWindowsVssSignature = args.erase_windows_vss_signature

    if self._support_post_key_revocation_action_type and args.IsSpecified(
        'post_key_revocation_action_type'):
      instance_properties.postKeyRevocationActionType = arg_utils.ChoiceToEnum(
          args.post_key_revocation_action_type, compute_client.messages.Instance
          .PostKeyRevocationActionTypeValueValuesEnum)

    if args.IsSpecified('network_performance_configs'):
      instance_properties.networkPerformanceConfig = (
          instance_utils.GetNetworkPerformanceConfig(args, compute_client))

    bulk_instance_resource = compute_client.messages.BulkInsertInstanceResource(
        count=instance_count,
        instanceProperties=instance_properties,
        minCount=instance_min_count,
        perInstanceProperties=per_instance_props,
        sourceInstanceTemplate=source_instance_template,
        namePattern=name_pattern,
        locationPolicy=location_policy)

    if scope == compute_scopes.ScopeEnum.ZONE:
      instance_service = compute_client.apitools_client.instances
      request_message = compute_client.messages.ComputeInstancesBulkInsertRequest(
          bulkInsertInstanceResource=bulk_instance_resource,
          project=project,
          zone=location)
    elif scope == compute_scopes.ScopeEnum.REGION:
      instance_service = compute_client.apitools_client.regionInstances
      request_message = compute_client.messages.ComputeRegionInstancesBulkInsertRequest(
          bulkInsertInstanceResource=bulk_instance_resource,
          project=project,
          region=location)

    return instance_service, request_message

  def Run(self, args):
    """Runs bulk create command.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      A resource object dispatched by display.Displayer().
    """

    instances_flags.ValidateBulkCreateArgs(args)
    if self._support_enable_target_shape:
      instances_flags.ValidateBulkTargetShapeArgs(args)
    instances_flags.ValidateLocationPolicyArgs(args)
    instances_flags.ValidateBulkDiskFlags(
        args,
        enable_source_snapshot_csek=self._support_source_snapshot_csek,
        enable_image_csek=self._support_image_csek)
    instances_flags.ValidateImageFlags(args)
    instances_flags.ValidateLocalSsdFlags(args)
    instances_flags.ValidateNicFlags(args)
    instances_flags.ValidateServiceAccountAndScopeArgs(args)
    instances_flags.ValidateAcceleratorArgs(args)
    instances_flags.ValidateNetworkTierArgs(args)
    instances_flags.ValidateReservationAffinityGroup(args)
    instances_flags.ValidateNetworkPerformanceConfigsArgs(args)
    instances_flags.ValidateInstanceScheduling(
        args, support_max_run_duration=self._support_max_run_duration)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = holder.client
    resource_parser = holder.resources

    project = properties.VALUES.core.project.GetOrFail()
    location = None
    scope = None

    if args.IsSpecified('zone'):
      location = args.zone
      scope = compute_scopes.ScopeEnum.ZONE
    elif args.IsSpecified('region'):
      location = args.region
      scope = compute_scopes.ScopeEnum.REGION

    instances_service, request = self._CreateRequests(args, holder,
                                                      compute_client,
                                                      resource_parser, project,
                                                      location, scope)

    self._errors = []
    self._log_async = False
    self._status_message = None

    if args.async_:
      self._log_async = True
      try:
        response = instances_service.BulkInsert(request)
        self._operation_selflink = response.selfLink
        return {'operationGroupId': response.operationGroupId}
      except exceptions.HttpException as error:
        raise error

    errors_to_collect = []
    response = compute_client.MakeRequests(
        [(instances_service, 'BulkInsert', request)],
        errors_to_collect=errors_to_collect,
        log_result=False,
        always_return_operation=True,
        no_followup=True)

    self._errors = errors_to_collect
    if response:
      operation_group_id = response[0].operationGroupId
      result = _GetResult(compute_client, request, operation_group_id)
      if result['createdInstanceCount'] is not None and result[
          'failedInstanceCount'] is not None:
        self._status_message = 'VM instances created: {}, failed: {}.'.format(
            result['createdInstanceCount'], result['failedInstanceCount'])
      return result
    return

  def Epilog(self, resources_were_displayed):
    del resources_were_displayed
    if self._errors:
      log.error(self._errors[0][1])
    elif self._log_async:
      log.status.Print('Bulk instance creation in progress: {}'.format(
          self._operation_selflink))
    else:
      if self._errors:
        log.warning(self._errors[0][1])
      log.status.Print(
          'Bulk create request finished with status message: [{}]'.format(
              self._status_message))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create Compute Engine virtual machine instances."""

  _support_display_device = True
  _support_secure_tags = False
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = False
  _support_visible_core_count = True
  _support_max_run_duration = False
  _support_enable_target_shape = True

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        deprecate_maintenance_policy=cls._deprecate_maintenance_policy,
        support_min_node_cpu=cls._support_min_node_cpu,
        support_erase_vss=cls._support_erase_vss,
        snapshot_csek=cls._support_source_snapshot_csek,
        image_csek=cls._support_image_csek,
        support_display_device=cls._support_display_device,
        support_local_ssd_size=cls._support_local_ssd_size,
        support_numa_node_count=cls._support_numa_node_count,
        support_visible_core_count=cls._support_visible_core_count,
        support_max_run_duration=cls._support_max_run_duration,
        support_enable_target_shape=cls._support_enable_target_shape)
    cls.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeBulkSourceInstanceTemplateArg())
    cls.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.BETA)
    instances_flags.AddPublicDnsArgs(parser, instance=True)
    instances_flags.AddConfidentialComputeArgs(parser)
    instances_flags.AddPostKeyRevocationActionTypeArgs(parser)
    instances_flags.AddBulkCreateArgs(parser)
    instances_flags.AddHostErrorTimeoutSecondsArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create Compute Engine virtual machine instances."""

  _support_display_device = True
  _support_local_ssd_size = True
  _support_secure_tags = True
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = True
  _support_visible_core_count = True
  _support_max_run_duration = True
  _support_enable_target_shape = True

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        deprecate_maintenance_policy=cls._deprecate_maintenance_policy,
        support_min_node_cpu=cls._support_min_node_cpu,
        support_erase_vss=cls._support_erase_vss,
        snapshot_csek=cls._support_source_snapshot_csek,
        image_csek=cls._support_image_csek,
        support_display_device=cls._support_display_device,
        support_local_ssd_size=cls._support_local_ssd_size,
        support_numa_node_count=cls._support_numa_node_count,
        support_visible_core_count=cls._support_visible_core_count,
        support_max_run_duration=cls._support_max_run_duration,
        support_enable_target_shape=cls._support_enable_target_shape)

    cls.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeBulkSourceInstanceTemplateArg())
    cls.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.ALPHA)
    instances_flags.AddPublicDnsArgs(parser, instance=True)
    instances_flags.AddConfidentialComputeArgs(parser)
    instances_flags.AddPostKeyRevocationActionTypeArgs(parser)
    instances_flags.AddBulkCreateArgs(parser)
    instances_flags.AddSecureTagsArgs(parser)
    instances_flags.AddHostErrorTimeoutSecondsArgs(parser)


Create.detailed_help = DETAILED_HELP
