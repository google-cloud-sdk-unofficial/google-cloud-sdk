# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""API client interactions for BigQuery migration cloud extraction."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import constants as compute_constants
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.logging import common as logging_common
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
import six

DEFAULT_MACHINE_TYPE = 'e2-micro'
DEFAULT_IMAGE_FAMILY = 'projects/debian-cloud/global/images/family/debian-13'
DEFAULT_DISK_SIZE_GB = 20
DEFAULT_SUBNET = 'default'
LABEL_KEY = 'goog-bqms-extractor-run-id'


class CloudExtractionError(exceptions.Error):
  """Raised when cloud extraction fails or finishes without an artifact."""


def _ParseNetworkRelativeName(project, network):
  """Returns the relative resource name for a Compute Engine network."""
  return resources.REGISTRY.Parse(
      network or compute_constants.DEFAULT_NETWORK,
      params={'project': project},
      collection='compute.networks',
  ).RelativeName()


def _ParseSubnetworkRelativeName(project, region, subnet):
  """Returns the relative resource name for a Compute Engine subnetwork."""
  return resources.REGISTRY.Parse(
      subnet or DEFAULT_SUBNET,
      params={'project': project, 'region': region},
      collection='compute.subnetworks',
  ).RelativeName()


def _FormatCloudArtifactTarget(output_uri):
  """Formats the GCS output URI for GCE `artifact_target` metadata."""
  if output_uri.lower().endswith('.zip') or output_uri.endswith('/'):
    return output_uri
  return output_uri + '/'


def CreateExtractorInstance(
    project,
    zone,
    region,
    instance_name,
    connector,
    output_uri,
    secret_name,
    sa_email,
    run_id,
    startup_script_url=None,
    network=None,
    subnet=None,
    no_address=False,
    compute_client=None,
):
  """Creates the Compute Engine VM that runs the cloud extractor.

  Args:
    project: str, The GCP project ID.
    zone: str, Target Compute Engine zone.
    region: str, Target region derived from `zone`.
    instance_name: str, Name of the Compute Engine instance to create.
    connector: str, Extractor connector name.
    output_uri: str, Target Cloud Storage URI (`gs://bucket/path`).
    secret_name: str, Secret Manager secret ID storing the dumper arguments.
    sa_email: str, Service account email to attach to the VM (or `''`).
    run_id: str, Unique run identifier used to label the VM.
    startup_script_url: str or None, Custom startup script URL override.
    network: str or None, Custom VPC network name or self-link.
    subnet: str or None, Custom subnet name or self-link.
    no_address: bool, If True, omit external IP (`accessConfigs`).
    compute_client: apitools client or None, Optional compute v1 client override
      for testing.

  Returns:
    str, The numeric instance ID as a string (or `''` if unavailable).

  Raises:
    CloudExtractionError: If the Compute Engine insert operation fails.
  """
  client = compute_client or apis.GetClientInstance('compute', 'v1')
  m = client.MESSAGES_MODULE

  resolved_script_url = (
      startup_script_url
      or 'gs://bqms-cloud-extractor-{}/launcher/gce_launcher.sh'.format(region)
  )
  log.status.Print('Using startup script URL: {}'.format(resolved_script_url))
  artifact_target = _FormatCloudArtifactTarget(output_uri)

  metadata = m.Metadata(
      items=[
          m.Metadata.ItemsValueListEntry(
              key='startup-script-url', value=resolved_script_url
          ),
          m.Metadata.ItemsValueListEntry(key='dwh_onfinish', value='delete'),
          m.Metadata.ItemsValueListEntry(key='connector', value=connector),
          m.Metadata.ItemsValueListEntry(
              key='artifact_target', value=artifact_target
          ),
          m.Metadata.ItemsValueListEntry(key='enable-oslogin', value='false'),
          m.Metadata.ItemsValueListEntry(
              key=compute_constants.SSH_KEYS_BLOCK_METADATA_KEY, value='true'
          ),
          m.Metadata.ItemsValueListEntry(key='secret_id', value=secret_name),
      ]
  )

  access_configs = []
  if not no_address:
    access_configs.append(
        m.AccessConfig(
            name=compute_constants.DEFAULT_ACCESS_CONFIG_NAME,
            networkTier=m.AccessConfig.NetworkTierValueValuesEnum.PREMIUM,
            type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT,
        )
    )

  network_interface = m.NetworkInterface(
      accessConfigs=access_configs,
      network=_ParseNetworkRelativeName(project, network),
      subnetwork=_ParseSubnetworkRelativeName(project, region, subnet),
      stackType=m.NetworkInterface.StackTypeValueValuesEnum.IPV4_ONLY,
  )

  service_accounts = []
  if sa_email:
    service_accounts.append(
        m.ServiceAccount(
            email=sa_email,
            scopes=list(compute_constants.SCOPES['cloud-platform']),
        )
    )

  disk_type = resources.REGISTRY.Parse(
      compute_constants.DISK_TYPE_PD_BALANCED,
      params={'project': project, 'zone': zone},
      collection='compute.diskTypes',
  ).RelativeName()
  boot_disk = m.AttachedDisk(
      autoDelete=True,
      boot=True,
      deviceName='instance-4',
      initializeParams=m.AttachedDiskInitializeParams(
          diskSizeGb=DEFAULT_DISK_SIZE_GB,
          diskType=disk_type,
          sourceImage=DEFAULT_IMAGE_FAMILY,
      ),
      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
  )

  labels = m.Instance.LabelsValue(
      additionalProperties=[
          m.Instance.LabelsValue.AdditionalProperty(
              key='cloud_extraction', value='gcloud'
          ),
          m.Instance.LabelsValue.AdditionalProperty(
              key=LABEL_KEY, value=run_id
          ),
      ]
  )

  instance = m.Instance(
      name=instance_name,
      machineType='zones/{}/machineTypes/{}'.format(zone, DEFAULT_MACHINE_TYPE),
      networkInterfaces=[network_interface],
      metadata=metadata,
      scheduling=m.Scheduling(
          automaticRestart=False,
          onHostMaintenance=(
              m.Scheduling.OnHostMaintenanceValueValuesEnum.MIGRATE
          ),
          provisioningModel=(
              m.Scheduling.ProvisioningModelValueValuesEnum.STANDARD
          ),
      ),
      serviceAccounts=service_accounts,
      disks=[boot_disk],
      shieldedInstanceConfig=m.ShieldedInstanceConfig(
          enableSecureBoot=False,
          enableVtpm=True,
          enableIntegrityMonitoring=True,
      ),
      labels=labels,
      reservationAffinity=m.ReservationAffinity(
          consumeReservationType=(
              m.ReservationAffinity.ConsumeReservationTypeValueValuesEnum.ANY_RESERVATION
          )
      ),
      keyRevocationActionType=(
          m.Instance.KeyRevocationActionTypeValueValuesEnum.STOP
      ),
  )

  log.status.Print('Launching instance {}...'.format(instance_name))
  operation = client.instances.Insert(
      m.ComputeInstancesInsertRequest(
          project=project, zone=zone, instance=instance
      )
  )
  operation_ref = resources.REGISTRY.Parse(
      operation.name,
      params={'project': project, 'zone': zone},
      collection='compute.zoneOperations',
  )
  instance_ref = resources.REGISTRY.Parse(
      instance_name,
      params={'project': project, 'zone': zone},
      collection='compute.instances',
  )
  operation_poller = poller.Poller(client.instances, target_ref=instance_ref)
  try:
    created_instance = waiter.WaitFor(
        operation_poller,
        operation_ref,
        'Waiting for instance [{}] to be created'.format(instance_name),
    )
    if created_instance and created_instance.id is not None:
      return six.text_type(created_instance.id)
  except poller.OperationErrors as err:
    raise CloudExtractionError(
        'Failed to create Compute Engine instance: {}'.format(err)
    ) from err
  except apitools_exceptions.HttpError:
    pass
  return ''


def GetInstanceStatus(project, zone, instance_name, compute_client=None):
  """Fetches the status of a Compute Engine instance.

  Args:
    project: str, The GCP project ID.
    zone: str, Compute Engine zone.
    instance_name: str, Compute Engine instance name.
    compute_client: apitools client or None, Optional compute v1 client override
      for testing.

  Returns:
    str or None, The instance status string (e.g. `'RUNNING'`, `'TERMINATED'`,
    `'UNKNOWN'`), or `None` if the instance was deleted (HTTP 404).
  """
  comp_client = compute_client or apis.GetClientInstance('compute', 'v1')
  comp_messages = comp_client.MESSAGES_MODULE
  try:
    instance = comp_client.instances.Get(
        comp_messages.ComputeInstancesGetRequest(
            project=project, zone=zone, instance=instance_name
        )
    )
    return (
        six.text_type(instance.status)
        if instance and instance.status
        else 'UNKNOWN'
    )
  except apitools_exceptions.HttpNotFoundError:
    return None
  except apitools_exceptions.HttpError:
    return 'UNKNOWN'


def FindOutputZipArtifact(output_ref, storage_client=None):
  """Returns `(gs_uri, size_bytes)` for the first non-empty `.zip` artifact."""
  stor_client = storage_client or storage_api.StorageClient()
  obj_path = output_ref.object or ''
  is_explicit_zip = obj_path.lower().endswith('.zip')
  if not obj_path:
    prefix = None
  elif is_explicit_zip:
    prefix = obj_path
  else:
    prefix = obj_path.rstrip('/') + '/'

  try:
    for obj in stor_client.ListBucket(output_ref.bucket_ref, prefix=prefix):
      name = obj.name
      size = obj.size or 0
      if not name or not name.lower().endswith('.zip') or size <= 0:
        continue
      if is_explicit_zip and name != prefix:
        continue
      if prefix and not is_explicit_zip and not name.startswith(prefix):
        continue
      return 'gs://{}/{}'.format(output_ref.bucket, name), size
  except (storage_api.Error, apitools_exceptions.HttpError):
    return None
  return None


def FetchInstanceErrorMessages(project, instance_id):
  """Fetches recent ERROR/SEVERE log messages for a Compute Engine instance.

  Args:
    project: str, The GCP project ID.
    instance_id: str, The numeric GCE instance ID.

  Returns:
    list[str], Extracted error messages (up to 5), or `[]` if none or on HTTP
    error.
  """
  if not instance_id:
    return []
  log_filter = (
      'resource.type="gce_instance" AND '
      'resource.labels.instance_id="{}" AND '
      '(severity>=ERROR OR textPayload:"ERROR" OR textPayload:"SEVERE") AND '
      'NOT textPayload:"instance-identity/document"'
  ).format(instance_id)

  messages = []
  try:
    entries = logging_common.FetchLogs(
        log_filter=log_filter,
        order_by='DESC',
        limit=5,
        parent='projects/{}'.format(project),
    )
    for entry in entries:
      if entry.textPayload:
        messages.append(entry.textPayload)
        continue
      json_payload = entry.jsonPayload
      if json_payload and json_payload.additionalProperties:
        for prop in json_payload.additionalProperties:
          if prop.key == 'message' and prop.value and prop.value.string_value:
            messages.append(six.text_type(prop.value.string_value))
            break
  except apitools_exceptions.HttpError:
    return []
  return messages
