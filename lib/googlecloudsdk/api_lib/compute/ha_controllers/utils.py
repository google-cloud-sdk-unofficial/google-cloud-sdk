# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Utilities for HA controllers."""

from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

PD_STANDARD_DISK_SIZE = 200
PD_SSD_OR_BALANCED_DISK_SIZE = 10
HYPERDISK_BALANCED_HA_DISK_SIZE = 4


def Insert(holder, ha_controller, ha_controller_ref, async_):
  """Inserts an HA Controller."""
  if not async_:
    return _Insert(ha_controller, ha_controller_ref, holder)
  return _ExecuteAsyncOperation(
      _InsertAsync, holder, ha_controller, ha_controller_ref,
      operation_type='creation'
  )


def Patch(holder, ha_controller, ha_controller_ref, async_):
  """Patches an HA Controller."""
  if not async_:
    return _Patch(ha_controller, ha_controller_ref, holder)
  return _ExecuteAsyncOperation(
      _PatchAsync, holder, ha_controller, ha_controller_ref,
      operation_type='update'
  )


def _CreateInsertRequest(client, ha_controller, ha_controller_ref):
  return client.messages.ComputeHaControllersInsertRequest(
      haController=ha_controller,
      project=ha_controller_ref.project,
      region=ha_controller_ref.region,
  )


def _Insert(ha_controller, ha_controller_ref, holder):
  request = _CreateInsertRequest(
      holder.client, ha_controller, ha_controller_ref
  )
  response = holder.client.apitools_client.haControllers.Insert(request)
  operation_ref = holder.resources.Parse(response.selfLink)
  return waiter.WaitFor(
      poller.Poller(holder.client.apitools_client.haControllers),
      operation_ref,
      message=(
          'HA controller creation in progress for [{}]: {}'.format(
              ha_controller.name, operation_ref.SelfLink()
          )
      ),
  )


def _InsertAsync(client, ha_controller, ha_controller_ref, errors_to_collect):
  request = _CreateInsertRequest(client, ha_controller, ha_controller_ref)
  return client.AsyncRequests(
      [(client.apitools_client.haControllers, 'Insert', request)],
      errors_to_collect
  )[0]


def _Patch(ha_controller, ha_controller_ref, holder):
  request = holder.client.messages.ComputeHaControllersPatchRequest(
      haController=ha_controller_ref.Name(),
      haControllerResource=ha_controller,
      project=ha_controller_ref.project,
      region=ha_controller_ref.region,
  )
  response = holder.client.apitools_client.haControllers.Patch(request)
  operation_ref = holder.resources.Parse(response.selfLink)
  return waiter.WaitFor(
      poller.Poller(holder.client.apitools_client.haControllers),
      operation_ref,
      message=(
          'HA controller update in progress for [{}]: {}'.format(
              ha_controller.name, operation_ref.SelfLink()
          )
      ),
  )


def _PatchAsync(client, ha_controller, ha_controller_ref, errors_to_collect):
  request = client.messages.ComputeHaControllersPatchRequest(
      haController=ha_controller_ref.Name(),
      haControllerResource=ha_controller,
      project=ha_controller_ref.project,
      region=ha_controller_ref.region,
  )
  return client.AsyncRequests(
      [(client.apitools_client.haControllers, 'Patch', request)],
      errors_to_collect
  )[0]


def Get(client, ha_controller_ref):
  """Send HA Controller get request."""
  return client.apitools_client.haControllers.Get(
      client.messages.ComputeHaControllersGetRequest(
          **ha_controller_ref.AsDict()
      )
  )


def GetInstance(client, instance_name, project, zone):
  """Returns the instance or throws an error if the instance cannot be found."""
  get_instance_request = client.messages.ComputeInstancesGetRequest(
      instance=instance_name,
      project=project,
      zone=zone,
  )
  return client.apitools_client.instances.Get(get_instance_request)


def GetFailedToGetInstanceErrorMessage(http_exception):
  """Returns the error message for a failed instance retrieval."""
  return utils.ConstructList(
      'Could not retrieve the instance. Check that the name and zone of your'
      ' instance are correct, and then retry the request:',
      utils.ParseErrors([api_exceptions.HttpException(http_exception)]),
  )


def StopInstance(client, instance_name, project, zone):
  """Performs a request to stop an instance and returns the error list, or an empty list if the request was successful."""
  errors = []
  stop_request = [(
      client.apitools_client.instances,
      'Stop',
      client.messages.ComputeInstancesStopRequest(
          instance=instance_name,
          project=project,
          zone=zone,
      ),
  )]
  client.MakeRequests(stop_request, errors_to_collect=errors)
  return errors


def GetFailedToStopInstanceErrorMessage(errors):
  """Returns the error message for a failed instance stop."""
  return utils.ConstructList(
      'Could not stop the instance. Check that the name and zone of your'
      ' instance are correct, and then retry your request. If this issue'
      ' persists, then inspect the instance and stop the instance manually:',
      ParseMakeRequestsErrors(errors),
  )


def GetZonalDisks(instance):
  """Returns the zonal disks for the given instance."""
  zonal_disks = []
  for disk in instance.disks:
    if '/zones/' in disk.source:
      zonal_disks.append(disk)
  return zonal_disks


def StartInstance(client, instance_name, project, zone):
  """Performs a request to start an instance and returns the error list, or an empty list if the request was successful."""
  errors = []
  start_request = [(
      client.apitools_client.instances,
      'Start',
      client.messages.ComputeInstancesStartRequest(
          instance=instance_name,
          project=project,
          zone=zone,
      ),
  )]
  client.MakeRequests(start_request, errors_to_collect=errors)
  return errors


def GetFailedToStartInstanceErrorMessage(errors):
  """Returns the error message for a failed instance start."""
  return utils.ConstructList(
      'Failed to start instance. It is recommended to manually start the'
      ' instance. If the issue persists, then contact your account team or'
      ' Google support:',
      ParseMakeRequestsErrors(errors),
  )


def _BuildDetachDiskRequest(client, instance_name, project, zone, disk):
  """Returns the request to detach a disk from an instance."""
  detach_request = (
      client.apitools_client.instances,
      'DetachDisk',
      client.messages.ComputeInstancesDetachDiskRequest(
          instance=instance_name,
          deviceName=disk.deviceName,
          project=project,
          zone=zone,
      ),
  )
  return detach_request


def DetachDisks(holder, instance_name, project, zone, disks):
  """Performs a batch request to detach disks from an instance and returns the error list, or an empty list if the request was successful."""
  requests = []
  for disk in disks:
    requests.append(
        _BuildDetachDiskRequest(
            holder.client, instance_name, project, zone, disk
        )
    )
  errors = []
  _ = list(
      request_helper.MakeRequests(
          requests=requests,
          http=holder.client.apitools_client.http,
          errors=errors,
          batch_url=holder.client.batch_url,
      )
  )
  return errors


def GetFailedToDetachDisksErrorMessage(errors, base_disk_type):
  """Returns the error message for a failed disks detachment."""
  return utils.ConstructList(
      f'Failed to detach {base_disk_type} disks. Check the instance and disk'
      ' details, ensure the instance is stopped, and then retry the request.'
      ' If the issue persists, then contact your account team or Google'
      ' support:',
      ParseMakeRequestsErrors(errors),
  )


def _BuildAttachDiskRequest(client, instance_name, project, zone, disk):
  """Returns the request to attach a disk to an instance."""
  attach_request = (
      client.apitools_client.instances,
      'AttachDisk',
      client.messages.ComputeInstancesAttachDiskRequest(
          instance=instance_name,
          project=project,
          zone=zone,
          attachedDisk=disk,
      ),
  )
  return attach_request


def AttachDisks(holder, instance_name, project, zone, disks):
  """Performs a batch request to attach disks to an instance and returns the error list, or an empty list if the request was successful."""
  requests = []
  for disk in disks:
    requests.append(
        _BuildAttachDiskRequest(
            holder.client, instance_name, project, zone, disk
        )
    )
  errors = []
  _ = list(
      request_helper.MakeRequests(
          requests=requests,
          http=holder.client.apitools_client.http,
          errors=errors,
          batch_url=holder.client.batch_url,
      )
  )
  return errors


def GetFailedToAttachDisksErrorMessage(errors, base_disk_type):
  """Returns the error message for a failed regional disks attachment."""
  return utils.ConstructList(
      f'Could not attach the {base_disk_type} disks:',
      ParseMakeRequestsErrors(errors),
  )


def BuildCreateSnapshotRequest(client, project, zone, disk):
  """Returns the request to create a disk snapshot and the snapshot name."""
  snapshot_name = _CreateSnapshotName(disk)
  snapshot_request = (
      client.apitools_client.disks,
      'CreateSnapshot',
      client.messages.ComputeDisksCreateSnapshotRequest(
          disk=disk.source.rsplit('/', 1).pop(),
          project=project,
          zone=zone,
          snapshot=client.messages.Snapshot(
              name=snapshot_name,
          ),
      ),
  )
  return snapshot_name, snapshot_request


def GetFailedToCreateSnapshotsErrorMessage(errors):
  """Returns the error message for a failed snapshots creation."""
  return utils.ConstructList(
      'Could not create snapshots. Check the details of the disks attached to'
      ' the provided instance, ensure that you have sufficient permissions to'
      ' create snapshots in this project, and then run the migration command'
      ' again. If the issue persists, then contact your account team or Google'
      ' support:',
      ParseMakeRequestsErrors(errors),
  )


def _BuildDeleteSnapshotRequest(client, project, snapshot_name):
  """Returns the request to delete a snapshot."""
  snapshot_request = (
      client.apitools_client.snapshots,
      'Delete',
      client.messages.ComputeSnapshotsDeleteRequest(
          project=project,
          snapshot=snapshot_name,
      ),
  )
  return snapshot_request


def DeleteSnapshots(holder, project, disks):
  """Performs a batch request to delete snapshots and returns the error list, or an empty list if the request was successful."""
  requests = []
  errors = []
  for disk in disks:
    requests.append(
        _BuildDeleteSnapshotRequest(
            holder.client, project, _CreateSnapshotName(disk)
        )
    )
  _ = list(
      request_helper.MakeRequests(
          requests=requests,
          http=holder.client.apitools_client.http,
          errors=errors,
          batch_url=holder.client.batch_url,
      )
  )
  return errors


def GetDiskMetadata(holder, project, region, zone, disk_resource):
  """Returns the disk metadata for the given disk resource."""
  if 'regions' in disk_resource.SelfLink():
    disk_response = holder.client.apitools_client.regionDisks.Get(
        holder.client.messages.ComputeRegionDisksGetRequest(
            project=project,
            region=region,
            disk=disk_resource.Name(),
        )
    )
  else:
    disk_response = holder.client.apitools_client.disks.Get(
        holder.client.messages.ComputeDisksGetRequest(
            project=disk_resource.project,
            zone=zone,
            disk=disk_resource.Name(),
        )
    )
  return disk_response


def GetMachineType(instance):
  """Returns the machine type for the given instance."""
  return instance.machineType.split('/')[-1].split('-')[0]


def CreateRegionalDiskName(holder, disk):
  """Returns the name of the regional disk to be created from the given zonal disk."""
  return f'r-{holder.resources.Parse(disk.source).Name()}'[:63].removesuffix(
      '-'
  )


def _CreateSnapshotName(disk):
  """Returns the temporary snapshot name for the given disk."""
  return 't-' + disk.source.rsplit('/', 1)[-1][:63].removesuffix('-')


def _BuildCreateRegionalDiskRequest(
    holder,
    project,
    region,
    zone,
    replica_zone,
    snapshot_url,
    source_disk,
    disk_metadata,
    destination_disk_type,
):
  """Returns the request to create a regional disk."""
  disk_size = source_disk.diskSizeGb
  min_disk_size = _GetMinDiskSize(destination_disk_type)
  if disk_size < min_disk_size:
    log.warning(
        GetDiskSizeChangeWarningMessage(
            holder.resources.Parse(source_disk.source).Name(),
            disk_size,
            min_disk_size,
        )
    )
    disk_size = min_disk_size
  disk_resource = holder.client.messages.Disk(
      name=CreateRegionalDiskName(holder, source_disk),
      sourceSnapshot=snapshot_url,
      replicaZones=[
          holder.resources.Create(
              'compute.zones', project=project, zone=zone
          ).SelfLink(),
          holder.resources.Create(
              'compute.zones', project=project, zone=replica_zone
          ).SelfLink(),
      ],
      sizeGb=disk_size,
      type=destination_disk_type,
      guestOsFeatures=[
          holder.client.messages.GuestOsFeature(
              type=holder.client.messages.GuestOsFeature.TypeValueValuesEnum.UEFI_COMPATIBLE,
          )
      ],
  )
  _UpdateDiskResourceMetadata(
      disk_resource, disk_metadata, destination_disk_type
  )
  _SetDiskResourceEncryptionKey(holder, source_disk, disk_resource)
  disk_request = (
      holder.client.apitools_client.regionDisks,
      'Insert',
      holder.client.messages.ComputeRegionDisksInsertRequest(
          disk=disk_resource,
          project=project,
          region=region,
      ),
  )
  return disk_request


def GetDiskSizeChangeWarningMessage(
    disk_name, original_disk_size, new_disk_size
):
  """Returns the warning message for the disk size change."""
  return (
      f'The {disk_name} disk does not meet the minimum size for a regional'
      f' disk. This command increases the disk size from {original_disk_size}'
      f' GB to {new_disk_size} GB.'
  )


def _GetMinDiskSize(disk_type):
  """Returns the minimum disk size for the given disk type."""
  if 'pd-standard' in disk_type:
    return PD_STANDARD_DISK_SIZE
  elif 'pd-ssd' in disk_type or 'pd-balanced' in disk_type:
    return PD_SSD_OR_BALANCED_DISK_SIZE
  elif 'hyperdisk-balanced-high-availability' in disk_type:
    return HYPERDISK_BALANCED_HA_DISK_SIZE
  return 0


def _UpdateDiskResourceMetadata(
    disk_resource, disk_metadata, destination_disk_type
):
  """Updates the disk resource metadata."""
  if destination_disk_type.startswith('hyperdisk'):
    disk_resource.provisionedIops = _NormalizeMetadataValues(
        disk_metadata.provisionedIops
    )
    disk_resource.provisionedThroughput = _NormalizeMetadataValues(
        disk_metadata.provisionedThroughput
    )
  disk_resource.description = _NormalizeMetadataValues(
      disk_metadata.description
  )
  disk_resource.labels = _NormalizeMetadataValues(disk_metadata.labels)
  disk_resource.resourcePolicies = _NormalizeMetadataValues(
      disk_metadata.resourcePolicies
  )
  disk_resource.accessMode = _NormalizeMetadataValues(disk_metadata.accessMode)
  disk_resource.guestOsFeatures.extend(
      _NormalizeMetadataValues(disk_metadata.guestOsFeatures)
  )
  disk_resource.guestOsFeatures = _NormalizeMetadataValues(
      disk_metadata.guestOsFeatures
  )


def _NormalizeMetadataValues(metadata_value):
  """Normalizes the disk metadata values."""
  return '' if metadata_value == 'None' else metadata_value


def _SetDiskResourceEncryptionKey(holder, source_disk, disk_resource):
  """Sets the disk encryption key for the given disk resource."""
  if source_disk.diskEncryptionKey and source_disk.diskEncryptionKey.kmsKeyName:
    kms_key = source_disk.diskEncryptionKey.kmsKeyName
    disk_resource.diskEncryptionKey = (
        holder.client.messages.CustomerEncryptionKey(
            kmsKeyName=kms_key,
        )
    )
    disk_resource.sourceSnapshotEncryptionKey = (
        holder.client.messages.CustomerEncryptionKey(
            kmsKeyName=kms_key,
        )
    )


def PerformCreateRegionalDiskBatchRequest(
    holder,
    project,
    region,
    zone,
    replica_zone,
    zonal_disks,
    disk_metadata,
    destination_disk_types,
):
  """Performs a batch request to create a regional disk and returns the error list, or an empty list if the request was successful."""
  requests = []
  for disk in zonal_disks:
    snapshot_url = holder.resources.Create(
        'compute.snapshots',
        project=project,
        snapshot=_CreateSnapshotName(disk),
    ).SelfLink()
    requests.append(
        _BuildCreateRegionalDiskRequest(
            holder,
            project,
            region,
            zone,
            replica_zone,
            snapshot_url,
            disk,
            disk_metadata[disk.deviceName],
            destination_disk_types[disk.deviceName],
        )
    )
  errors = []
  _ = list(
      request_helper.MakeRequests(
          requests=requests,
          http=holder.client.apitools_client.http,
          errors=errors,
          batch_url=holder.client.batch_url,
      )
  )
  return errors


def GetFailedToCreateRegionalDisksErrorMessage(errors):
  """Returns the error message for a failed regional disks creation."""
  return utils.ConstructList(
      'Could not create regional disks:', ParseMakeRequestsErrors(errors)
  )


def _BuildDeleteRegionalDiskRequest(holder, project, region, disk_name):
  """Returns the request to delete a regional disk."""
  disk_request = (
      holder.client.apitools_client.regionDisks,
      'Delete',
      holder.client.messages.ComputeRegionDisksDeleteRequest(
          project=project,
          region=region,
          disk=disk_name,
      ),
  )
  return disk_request


def PerformDeleteRegionalDiskBatchRequest(holder, project, region, zonal_disks):
  """Performs a batch request to delete a regional disk and returns the error list, or an empty list if the request was successful."""
  requests = []
  errors = []
  for disk in zonal_disks:
    requests.append(
        _BuildDeleteRegionalDiskRequest(
            holder, project, region, CreateRegionalDiskName(holder, disk)
        )
    )
  _ = list(
      request_helper.MakeRequests(
          requests=requests,
          http=holder.client.apitools_client.http,
          errors=errors,
          batch_url=holder.client.batch_url,
      )
  )
  return errors


def ParseMakeRequestsErrors(errors):
  """Parses errors returned by MakeRequests (list of tuples) or parse an error directly if it is not a tuple."""
  parsed_errors = []
  for error in errors:
    if isinstance(error, tuple):
      if len(error) > 1:
        parsed_errors.append(error[1])
      elif len(error) == 1:
        parsed_errors.append(error[0])
    else:
      parsed_errors.append(error)
  return utils.ParseErrors(parsed_errors)


def _HandleAsyncResponse(response, holder, ha_controller_name, operation_type):
  """Handles the response from an asynchronous HA Controller operation."""
  err = getattr(response, 'error', None)
  if err:
    raise core_exceptions.MultiError([poller.OperationErrors(err.errors)])

  operation_ref = holder.resources.Parse(response.selfLink)

  log.status.Print(
      'HA Controller {} in progress for [{}]: {}'.format(
          operation_type, ha_controller_name, operation_ref.SelfLink()
      )
  )
  log.status.Print(
      'Use [gcloud compute operations describe URI] command '
      'to check the status of the operation.'
  )
  return response


def _ExecuteAsyncOperation(
    async_method, holder, ha_controller, ha_controller_ref, operation_type
):
  """Executes an asynchronous HA Controller operation."""
  errors_to_collect = []
  response = async_method(
      holder.client, ha_controller, ha_controller_ref, errors_to_collect
  )
  if errors_to_collect:
    raise core_exceptions.MultiError(errors_to_collect)
  return _HandleAsyncResponse(
      response, holder, ha_controller.name, operation_type
  )
