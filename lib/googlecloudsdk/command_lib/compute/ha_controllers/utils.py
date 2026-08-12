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
"""Flags for the compute ha-controllers commands."""

import collections

from apitools.base.protorpclite import messages
from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.ha_controllers import utils as api_utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io


_MESSAGES = apis.GetMessagesModule("compute", "alpha")

SUPPORTED_DISK_TYPES = {
    "e2": "Regional PD",
    "n1": "Regional PD",
    "n2": "Regional PD",
    "n2d": "Regional PD",
    "a3": "Hyperdisk HA",
    "a4": "Hyperdisk HA",
    "c3": "Hyperdisk HA",
    "c3d": "Hyperdisk HA",
    "c4": "Hyperdisk HA",
    "c4a": "Hyperdisk HA",
    "g4": "Hyperdisk HA",
    "m3": "Hyperdisk HA",
    "n4": "Hyperdisk HA",
    "n4a": "Hyperdisk HA",
    "n4d": "Hyperdisk HA",
    "z3": "Hyperdisk HA",
}

FAILED_MIGRATION_ERROR_MESSAGE = (
    "Failed to migrate zonal disks to regional disks. Check the logs for"
    " more details."
)
CSEK_ERROR_MESSAGE = (
    "You cannot migrate disks that use customer-supplied encryption keys"
    " (CSEK)."
)
PD_EXTREME_ERROR_MESSAGE = (
    "Google Cloud does not support regional pd-extreme disks."
)
CONFIDENTIAL_VM_ERROR_MESSAGE = (
    "Boot disks for Confidential VMs must remain zonal. Confidential VMs"
    " do not support regional boot disks."
)
MACHINE_MISMATCH_ERROR_MESSAGE = (
    "This machine series cannot use Hyperdisk Balanced HA. It only"
    " supports Regional PD."
)


def GetFailedToRollbackSnapshotsErrorMessage(errors):
  """Returns the error message for a failed snapshots rollback."""
  return utils.ConstructList(
      "Could not delete temporary snapshots. Delete these snapshots manually:",
      api_utils.ParseMakeRequestsErrors(errors),
  )


def GetFailedToDeleteSnapshotsWarningMessage(errors):
  """Returns the warning message for a failed snapshots deletion."""
  return utils.ConstructList(
      "Could not delete temporary snapshots. This issue does not block the"
      " migration, but you should delete these snapshots manually:",
      api_utils.ParseMakeRequestsErrors(errors),
  )


def GetFailedToRollbackRegionalDisksCreationWarningMessage(errors):
  """Returns the warning message for a failed regional disks creation rollback."""
  return utils.ConstructList(
      "Could not delete the regional disks created during the migration. You"
      " should delete these disks manually:",
      api_utils.ParseMakeRequestsErrors(errors),
  )


def GetFailedToReattachZonalDisksWarningMessage(errors):
  """Returns the warning message for a failed zonal disks reattachment."""
  return utils.ConstructList(
      "Could not reattach zonal disks to your instance. You must manually"
      " check the disk attachments:",
      api_utils.ParseMakeRequestsErrors(errors),
  )


def GetMessagesModule(version="alpha"):
  return apis.GetMessagesModule("compute", version)


class NodeAffinityFileParseError(core_exceptions.Error):
  """Exception for invalid node affinity file format."""


def AddHaControllerNameArgToParser(parser, api_version=None):
  """Adds an HA Controller name resource_data argument."""
  ha_controller_data = yaml_data.ResourceYAMLData.FromPath(
      "compute.ha_controllers.ha_controller"
  )
  resource_data_spec = concepts.ResourceSpec.FromYaml(
      ha_controller_data.GetData(), is_positional=True, api_version=api_version
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name="ha_controller",
      concept_spec=resource_data_spec,
      required=True,
      group_help="Name of an HA Controller.",
  )
  concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def MakeZoneConfiguration(
    zone_config: list[dict[str, str]],
) -> _MESSAGES.HaController.ZoneConfigurationsValue:
  """Convert zone-configuration to the zoneConfigurations api field."""
  zone_configs_parsed: list[
      _MESSAGES.HaController.ZoneConfigurationsValue.AdditionalProperty
  ] = []
  if len(zone_config) == 1:
    if console_io.CanPrompt() and not console_io.PromptContinue(
        "Only one zone configuration was specified. Is it the primary zone? If"
        " so, should the secondary zone and the reservation affinities"
        " of the primary zone be inferred automatically?",
        default=False,
    ):
      raise compute_exceptions.AbortedError(
          "Please rerun the command with both zone configurations specified."
      )
  for config in zone_config:
    if "zone" not in config:
      continue
    single_zone_config = {}
    if "reservation-affinity" in config:
      single_zone_config["reservationAffinity"] = (
          _MESSAGES.HaControllerZoneConfigurationReservationAffinity(
              consumeReservationType=_MESSAGES.HaControllerZoneConfigurationReservationAffinity.ConsumeReservationTypeValueValuesEnum(
                  config["reservation-affinity"],
              )
          )
      )
      if "reservation" in config:
        single_zone_config["reservationAffinity"].key = (
            "compute."
            + properties.VALUES.core.universe_domain.Get()
            + "/reservation-name"
        )
        single_zone_config["reservationAffinity"].values = [
            config["reservation"]
        ]
    node_affinities = _GetNodeAffinities(config)
    if node_affinities:
      single_zone_config["nodeAffinities"] = node_affinities

    zone_configs_parsed.append(
        _MESSAGES.HaController.ZoneConfigurationsValue.AdditionalProperty(
            key=config["zone"],
            value=_MESSAGES.HaControllerZoneConfiguration(
                **single_zone_config
            ),
        )
    )

  res = _MESSAGES.HaController.ZoneConfigurationsValue(
      additionalProperties=zone_configs_parsed
  )
  return res


def MakeNetworkConfiguration(
    network_config: list[dict[str, str]],
) -> _MESSAGES.HaControllerNetworkingAutoConfiguration:
  """Convert network-auto-configuration args to the networkConfiguration api field."""
  network_config_parsed = {}
  if network_config and len(network_config) > 1:
    raise calliope_exceptions.InvalidArgumentException(
        "--network-auto-configuration",
        "Only one network interface can be specified.",
    )
  if not network_config:
    return None

  network_config = network_config[0]

  if "stack-type" in network_config:
    network_config_parsed["stackType"] = network_config["stack-type"]
  if "address" in network_config:
    network_config_parsed["ipAddress"] = network_config["address"]
  if "internal-ipv6-address" in network_config:
    network_config_parsed["ipv6Address"] = (
        network_config["internal-ipv6-address"]
    )

  return _MESSAGES.HaControllerNetworkingAutoConfiguration(
      internal=_MESSAGES.HaControllerNetworkingAutoConfigurationInternal(
          **network_config_parsed
      )
  )


def SetResourceName(unused_ref, unused_args, request):
  """Set resource_data.name to the provided haController ID.

  Args:
    unused_ref: An unused resource_data ref to the parsed resource_data.
    unused_args: The unused argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.
  """
  if hasattr(request.haControllerResource, "name"):
    request.haControllerResource.name = request.haController
  return request


def _GetNodeAffinities(config: dict[str, str]) -> list[
    _MESSAGES.HaControllerZoneConfigurationNodeAffinity
]:
  """Get node affinities from the zone configuration."""
  node_affinity_operator_enum = (
      _MESSAGES.HaControllerZoneConfigurationNodeAffinity.OperatorValueValuesEnum
  )
  node_affinities = []

  if "node-affinity-file" in config:
    affinities_yaml = yaml.load(config["node-affinity-file"])
    if not affinities_yaml:  # Catch empty files/lists.
      raise NodeAffinityFileParseError(
          "No node affinity labels specified. You must specify at least one "
          "label to create a sole tenancy instance."
      )
    for affinity in affinities_yaml:
      if not affinity:  # Catches None and empty dicts
        raise NodeAffinityFileParseError("Empty list item in JSON/YAML file.")
      try:
        node_affinity = encoding.PyValueToMessage(
            _MESSAGES.HaControllerZoneConfigurationNodeAffinity,
            affinity,
        )
      except Exception as e:  # pylint: disable=broad-except
        raise NodeAffinityFileParseError(e)
      if not node_affinity.key:
        raise NodeAffinityFileParseError(
            "A key must be specified for every node affinity label."
        )
      if node_affinity.all_unrecognized_fields():
        raise NodeAffinityFileParseError(
            "Key [{0}] has invalid field formats for: {1}".format(
                node_affinity.key, node_affinity.all_unrecognized_fields()
            )
        )

      node_affinities.append(node_affinity)
  if "node-group" in config:
    node_affinities.append(
        _MESSAGES.HaControllerZoneConfigurationNodeAffinity(
            key="compute."
            + properties.VALUES.core.universe_domain.Get()
            + "/node-group-name",
            operator=node_affinity_operator_enum.IN,
            values=[config["node-group"]],
        )
    )
  if "node" in config:
    node_affinities.append(
        _MESSAGES.HaControllerZoneConfigurationNodeAffinity(
            key="compute."
            + properties.VALUES.core.universe_domain.Get()
            + "/node-name",
            operator=node_affinity_operator_enum.IN,
            values=[config["node"]],
        )
    )
  if "node-project" in config:
    node_affinities.append(
        _MESSAGES.HaControllerZoneConfigurationNodeAffinity(
            key="compute."
            + properties.VALUES.core.universe_domain.Get()
            + "/project",
            operator=node_affinity_operator_enum.IN,
            values=[config["node-project"]],
        )
    )
  return node_affinities


def EnumTypeToChoices(enum_type: messages.Enum) -> str:
  """Converts an enum type to a comma-separated list of choices."""
  return ", ".join(
      c
      for c in sorted(
          [arg_utils.EnumNameToChoice(n) for n in enum_type.names()]
      )
  )


def FixExportStructure(
    resource_data: dict[str, str]) -> dict[str, str]:
  """Changes the API structure to the export structure."""
  if "zoneConfigurations" in resource_data:
    resource_data["zoneConfiguration"] = resource_data["zoneConfigurations"]
    del resource_data["zoneConfigurations"]
  if (
      "networkingAutoConfiguration" in resource_data
      and "internal" in resource_data["networkingAutoConfiguration"]
  ):
    resource_data["networkingAutoConfiguration"] = resource_data[
        "networkingAutoConfiguration"
    ]["internal"]
  return resource_data


def FixImportStructure(
    resource_data: dict[str, str]) -> dict[str, str]:
  """Changes and completes the export structure to the API structure."""
  if "zoneConfiguration" in resource_data:
    resource_data["zoneConfigurations"] = resource_data["zoneConfiguration"]
    del resource_data["zoneConfiguration"]
  if ("networkingAutoConfiguration" in resource_data):
    resource_data["networkingAutoConfiguration"] = {"internal": resource_data[
        "networkingAutoConfiguration"
    ]}
  return resource_data


def MigrateZonalDisksToRegional(
    holder, instance_name, project, region, zone, replica_zone
):
  """Migrates zonal disks of the instance to regional disks."""
  log.status.Print("Starting zonal to regional disks migration.")
  start_instance_needed = False
  try:
    instance = _PerformGetInstanceStep(holder, instance_name, project, zone)
    machine_type = api_utils.GetMachineType(instance)
    if machine_type not in SUPPORTED_DISK_TYPES:
      unsupported_machine_type_error_message = (
          GetUnsupportedMachineSeriesErrorMessage(machine_type)
      )
      log.error(unsupported_machine_type_error_message)
      raise calliope_exceptions.ToolException(
          unsupported_machine_type_error_message
      )
    zonal_disks = api_utils.GetZonalDisks(instance)
    if not zonal_disks:
      log.status.Print("No zonal disks found. Migration not needed.")
      return
    disk_metadata = _GetDisksMetadata(
        holder, project, region, zone, zonal_disks
    )
    _ValidateDiskMetadata(zonal_disks, disk_metadata)
    destination_disk_types = _GetDestinationDiskTypes(
        project,
        region,
        disk_metadata,
        SUPPORTED_DISK_TYPES[machine_type],
    )
    start_instance_needed = _PerformStopInstanceStep(
        holder, instance_name, project, zone
    )
    _PerformCreateSnapshotsOrRollbackStep(holder, project, zone, zonal_disks)
    _PerformCreateRegionalDisksOrRollbackStep(
        holder,
        project,
        region,
        zone,
        replica_zone,
        zonal_disks,
        disk_metadata,
        destination_disk_types,
    )
    _PerformDetachZonalDisksOrRollbackStep(
        holder, instance_name, project, zone, region, zonal_disks
    )
    _PerformAttachRegionalDisksOrRollbackStep(
        holder, instance_name, project, zone, region, zonal_disks
    )
  except calliope_exceptions.ToolException as e:
    raise calliope_exceptions.ToolException(
        FAILED_MIGRATION_ERROR_MESSAGE
    ) from e
  finally:
    if start_instance_needed:
      _PerformStartInstanceStep(holder, instance_name, project, zone)
  log.status.Print("Zonal to regional disks migration completed.")


def _GetRegionalDisksToAttach(holder, project, region, zonal_disks):
  """Returns the regional disks that should be attached as part of the migration process."""
  regional_disks = []
  for disk in zonal_disks:
    regional_disk_name = api_utils.CreateRegionalDiskName(holder, disk)
    disk_to_attach = holder.client.messages.AttachedDisk(
        deviceName=regional_disk_name,
        type=holder.client.messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
        mode=holder.client.messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
        source=holder.resources.Create(
            "compute.regionDisks",
            project=project,
            region=region,
            disk=regional_disk_name,
        ).SelfLink(),
        boot=disk.boot,
        autoDelete=disk.autoDelete,
    )
    regional_disks.append(disk_to_attach)
  return regional_disks


def _GetDestinationDiskTypes(
    project, region, disks_with_metadata, machine_type
):
  """Returns the regional disk types that should be used when converting the given zonal disks."""
  destination_disk_types = {}
  for device_name, metadata in disks_with_metadata.items():

    disk_type = metadata.type
    destination_type = metadata.type
    if machine_type == "Hyperdisk HA":
      if (
          disk_type.split("/")[-1].startswith("pd")
          or disk_type.split("/")[-1] == "hyperdisk-balanced"
      ):
        destination_type = (
            disk_type.rsplit("/projects/", 1)[0]
            + f"/projects/{project}/regions/{region}/diskTypes/hyperdisk-balanced-high-availability"
        )
    else:
      if disk_type.split("/")[-1] == "hyperdisk-balanced":
        log.error(MACHINE_MISMATCH_ERROR_MESSAGE)
        raise calliope_exceptions.ToolException(MACHINE_MISMATCH_ERROR_MESSAGE)
    if destination_type != disk_type:
      log.status.Print(
          f"Converting storage family from {disk_type} to {destination_type}"
          " for machine compatibility."
      )
    destination_disk_types[device_name] = destination_type
  return destination_disk_types


def _GetDisksMetadata(holder, project, region, zone, disks):
  """Returns the metadata for the given disks."""
  disks_with_metadata = {}
  for disk in disks:
    zonal_disk_resource = holder.resources.Parse(disk.source)
    disks_with_metadata[disk.deviceName] = api_utils.GetDiskMetadata(
        holder, project, region, zone, zonal_disk_resource
    )
  return disks_with_metadata


def _ValidateDiskMetadata(disks, disk_metadata):
  """Validates the disk metadata."""
  error_message = ""
  for disk in disks:
    if (
        disk_metadata[disk.deviceName].diskEncryptionKey
        and disk_metadata[disk.deviceName].diskEncryptionKey.sha256
    ):
      error_message = CSEK_ERROR_MESSAGE
    elif disk_metadata[disk.deviceName].type.endswith("pd-extreme"):
      error_message = PD_EXTREME_ERROR_MESSAGE
    elif disk.boot and disk_metadata[disk.deviceName].enableConfidentialCompute:
      error_message = CONFIDENTIAL_VM_ERROR_MESSAGE
    if error_message:
      log.error(error_message)
      raise calliope_exceptions.ToolException(error_message)


def _GetMachineTypesPerDiskTypeDict():
  """Returns a dictionary where keys are disk types and values are lists of machine types that support that disk type."""
  reversed_dict = collections.defaultdict(list)
  for machine_type, disk_type in SUPPORTED_DISK_TYPES.items():
    reversed_dict[disk_type].append(machine_type)
  return reversed_dict


def GetUnsupportedMachineSeriesErrorMessage(machine_series):
  """Returns the error message for an unsupported machine type."""
  disk_type_dict = _GetMachineTypesPerDiskTypeDict()
  error_message = (
      f"Machine series '{machine_series}' does not support regional storage"
      f" ({', '.join(disk_type_dict.keys())}).\n"
  )
  for disk_type, machine_types in disk_type_dict.items():
    error_message += (
        f"Supported series for {disk_type}:"
        f' {", ".join(machine_types).upper()}.\n'
    )
  return error_message


def _PerformGetInstanceStep(holder, instance_name, project, zone):
  """Gets the instance as part of the migration process."""
  try:
    return api_utils.GetInstance(holder.client, instance_name, project, zone)
  except apitools_exceptions.HttpError as e:
    log.error(api_utils.GetFailedToGetInstanceErrorMessage(e))
    http_exception = api_exceptions.HttpException(e)
    utils.RaiseToolException(
        problems=[
            (http_exception.payload.status_code, http_exception.payload.message)
        ],
        error_message="Failed to get instance.",
    )


def _PerformStopInstanceStep(holder, instance_name, project, zone):
  """Stops the instance as part of the migration process and returns True if the instance was stopped successfully, raises an exception otherwise."""
  log.status.Print("Stopping the instance...")
  errors = api_utils.StopInstance(holder.client, instance_name, project, zone)
  if errors:
    log.error(api_utils.GetFailedToStopInstanceErrorMessage(errors))
    utils.RaiseToolException(
        problems=errors,
        error_message="Failed to stop instance.",
    )
  return True


def _PerformStartInstanceStep(holder, instance_name, project, zone):
  """Starts the instance as part of the migration process."""
  log.status.Print("Starting the instance...")
  errors = api_utils.StartInstance(holder.client, instance_name, project, zone)
  if errors:
    log.warning(api_utils.GetFailedToStartInstanceErrorMessage(errors))


def _PerformCreateSnapshotsOrRollbackStep(holder, project, zone, zonal_disks):
  """Creates snapshots for the given zonal disks and attempts to delete them in case of errors."""
  requests = []
  for disk in zonal_disks:
    requests.append(
        api_utils.BuildCreateSnapshotRequest(holder.client, project, zone, disk)
    )
  log.status.Print("Creating snapshots...")
  errors = []
  _ = list(
      request_helper.MakeRequests(
          requests=[item[1] for item in requests],
          http=holder.client.apitools_client.http,
          errors=errors,
          batch_url=holder.client.batch_url,
          always_return_operation=True,
      )
  )
  if errors:
    log.error(api_utils.GetFailedToCreateSnapshotsErrorMessage(errors))
    log.status.Print("Performing rollback...")
    additional_errors = api_utils.DeleteSnapshots(holder, project, zonal_disks)
    if additional_errors:
      log.warning(
          GetFailedToRollbackSnapshotsErrorMessage(additional_errors),
      )
    utils.RaiseToolException(
        problems=errors,
        error_message="Failed to create snapshots.",
    )


def _PerformCreateRegionalDisksOrRollbackStep(
    holder,
    project,
    region,
    zone,
    replica_zone,
    zonal_disks,
    disk_metadata,
    destination_disk_types,
):
  """Creates regional disks for the given zonal disks, cleans up snapshots as part of the migration process and performs rollback operations in case of errors."""
  log.status.Print("Creating regional disks...")
  errors = api_utils.PerformCreateRegionalDiskBatchRequest(
      holder,
      project,
      region,
      zone,
      replica_zone,
      zonal_disks,
      disk_metadata,
      destination_disk_types,
  )
  log.status.Print("Deleting snapshots...")
  additional_errors = api_utils.DeleteSnapshots(holder, project, zonal_disks)
  if additional_errors:
    log.warning(GetFailedToDeleteSnapshotsWarningMessage(additional_errors))
  if errors:
    log.error(api_utils.GetFailedToCreateRegionalDisksErrorMessage(errors))
    log.status.Print("Performing rollback...")
    _RemoveExistingRegionalDisksFromRollback(errors, zonal_disks)
    RollbackRegionalDisksCreation(holder, project, region, zonal_disks)
    utils.RaiseToolException(
        problems=errors,
        error_message="Failed to create regional disks.",
    )


def _RemoveExistingRegionalDisksFromRollback(errors, zonal_disks):
  """Because _PerformCreateRegionalDisksOrRollbackStep might fail due to existing regional disks with the same name, this function removes those disks from the rollback list."""
  for error in errors:
    if isinstance(error, tuple) and len(error) > 1:
      if error[0] == 409 and error[1].endswith("already exists"):
        for disk in zonal_disks:
          if disk.deviceName in error[1]:
            zonal_disks.remove(disk)
            break


def _PerformDetachZonalDisksOrRollbackStep(
    holder, instance_name, project, zone, region, zonal_disks
):
  """Detaches zonal disks from the instance as part of the migration process and performs rollback operations in case of errors."""
  log.status.Print("Detaching zonal disks...")
  zonal_disks = zonal_disks.copy()
  errors = api_utils.DetachDisks(
      holder, instance_name, project, zone, zonal_disks
  )
  if errors:
    log.error(api_utils.GetFailedToDetachDisksErrorMessage(errors, "zonal"))
    log.status.Print("Performing rollback...")
    RollbackRegionalDisksCreation(holder, project, region, zonal_disks)
    additional_errors = api_utils.AttachDisks(
        holder, instance_name, project, zone, zonal_disks
    )
    if additional_errors:
      log.warning(
          GetFailedToReattachZonalDisksWarningMessage(additional_errors)
      )
    utils.RaiseToolException(
        problems=errors,
        error_message="Failed to detach zonal disks.",
    )


def _PerformAttachRegionalDisksOrRollbackStep(
    holder, instance_name, project, zone, region, zonal_disks
):
  """Attaches regional disks to the instance as part of the migration process and performs rollback operations in case of errors."""
  log.status.Print("Attaching regional disks...")
  regional_disks = _GetRegionalDisksToAttach(
      holder, project, region, zonal_disks
  )
  errors = api_utils.AttachDisks(
      holder, instance_name, project, zone, regional_disks
  )
  if errors:
    log.error(api_utils.GetFailedToAttachDisksErrorMessage(errors, "regional"))
    log.status.Print("Performing rollback...")
    RollbackRegionalDiskAttachment(
        holder,
        instance_name,
        project,
        zone,
        region,
        regional_disks,
        zonal_disks,
    )
    utils.RaiseToolException(
        problems=errors,
        error_message="Failed to attach regional disks.",
    )


def RollbackRegionalDisksCreation(holder, project, region, zonal_disks):
  """Rolls back the creation of regional disks."""
  if not zonal_disks:
    return
  errors = api_utils.PerformDeleteRegionalDiskBatchRequest(
      holder, project, region, zonal_disks
  )
  if errors:
    log.warning(GetFailedToRollbackRegionalDisksCreationWarningMessage(errors))


def RollbackRegionalDiskAttachment(
    holder, instance_name, project, zone, region, regional_disks, zonal_disks
):
  """Rolls back the attachment of regional disks by detaching them, attaching the zonal disks, and deleting the regional disks."""
  log.status.Print("Rolling back regional disk attachment...")
  errors = api_utils.DetachDisks(
      holder, instance_name, project, zone, regional_disks
  )
  if errors:
    log.error(api_utils.GetFailedToDetachDisksErrorMessage(errors, "regional"))
    return
  log.status.Print("Reattaching zonal disks...")
  errors = api_utils.AttachDisks(
      holder, instance_name, project, zone, zonal_disks
  )
  if errors:
    log.error(GetFailedToReattachZonalDisksWarningMessage(errors))
    return
  log.status.Print("Deleting leftover regional disks...")
  RollbackRegionalDisksCreation(holder, project, region, zonal_disks)
