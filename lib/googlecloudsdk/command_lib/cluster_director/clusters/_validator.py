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

"""Compute configuration utilities for clusters command group."""

from __future__ import annotations

import re
from typing import Any

from googlecloudsdk.command_lib.cluster_director.clusters import errors

ClusterDirectorError = errors.ClusterDirectorError


def ValidateFilestoreCapacity(capacity_gb: int) -> None:
  """Validates that Filestore capacity is between 1024 and 102400 GiB."""
  if capacity_gb < 1024 or capacity_gb > 102400:
    raise ClusterDirectorError(
        "Filestore capacity must be between 1024 and 102400 GiB, found"
        f" {capacity_gb} GiB."
    )


def ValidateLustreCapacity(capacity_gb: int) -> None:
  """Validates that Lustre capacity is between 18000 and 7632000 GiB."""
  if capacity_gb < 18000 or capacity_gb > 7632000:
    raise ClusterDirectorError(
        "Lustre capacity must be between 18000 and 7632000 GiB, found"
        f" {capacity_gb} GiB."
    )


def ValidateLustreDynamicTierOptions(mode: Any, message_module: Any) -> None:
  """Validates that Lustre dynamic tier options are DEFAULT_CACHE or DISABLED.

  Args:
    mode: The dynamic tier mode to validate.
    message_module: The API message module.

  Raises:
    ClusterDirectorError: If the mode is not valid.
  """
  if mode is None:
    return

  valid_modes = [
      message_module.DynamicTierOptions.ModeValueValuesEnum.DEFAULT_CACHE,
      message_module.DynamicTierOptions.ModeValueValuesEnum.DISABLED,
  ]
  if str(mode) not in [m.name for m in valid_modes]:
    raise ClusterDirectorError(
        "Lustre dynamic tier options mode must be one of DEFAULT_CACHE or"
        " DISABLED."
    )


def ValidateGcsBucketExclusiveOptions(
    has_storage_class: bool, has_autoclass: bool
) -> None:
  """Validates that storageClass and autoclass are not both specified."""
  if has_storage_class and has_autoclass:
    raise ClusterDirectorError(
        "Only one of storageClass or enableAutoclass can be set for a Cloud"
        " Storage bucket."
    )


def ValidateResourceID(resource_id: str) -> None:
  """Validates that a resource ID conforms to RFC-1034 / length limit."""
  if not re.match(r"^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$", resource_id):
    raise ClusterDirectorError(
        f"Resource ID '{resource_id}' must be 1-63 characters, lower-case"
        " alphanumeric or hyphen, start with a letter."
    )


def ValidateStorageConfigs(
    valid_storage_resources_map: dict[str, Any],
    storage_configs: list[Any],
    existing_mounts_by_id: dict[str, str],
) -> None:
  """Validates node set storage configs against the cluster's storage.

  Args:
    valid_storage_resources_map: Map of storage ID to StorageResource.
    storage_configs: The list of StorageConfig dictionary objects to validate.
    existing_mounts_by_id: Map of existing storage ID to its localMount path.

  Raises:
    ClusterDirectorError: If input fails rules.
  """
  seen_mounts = set()
  for sc in storage_configs or []:
    storage_id = sc.get("id")
    local_mount = sc.get("localMount")

    if not local_mount:
      raise ClusterDirectorError(
          f"The storage config '{storage_id}' is missing a local mount."
      )

    if not local_mount.startswith("/"):
      raise ClusterDirectorError(
          f"The storage config '{storage_id}' has a local mount"
          f" '{local_mount}', which does not start with a forward slash."
      )

    if local_mount in seen_mounts:
      raise ClusterDirectorError(
          f"The storage config '{storage_id}' has a local mount"
          f" '{local_mount}', which is already used by another storage config."
      )
    seen_mounts.add(local_mount)

    if storage_id not in valid_storage_resources_map:
      raise ClusterDirectorError(
          f"Storage resource [{storage_id}] does not exist in the cluster."
      )

    if storage_id in existing_mounts_by_id:
      if local_mount != existing_mounts_by_id[storage_id]:
        raise ClusterDirectorError(
            "Cannot update the localMount of already existing storage "
            f"[{storage_id}]."
        )

    if local_mount == "/home":
      continue

    storage_resource = valid_storage_resources_map[storage_id]
    if not storage_resource or not hasattr(storage_resource, "config"):
      continue

    config = storage_resource.config
    if not config:
      continue

    if getattr(config, "newFilestore", None) or getattr(
        config, "existingFilestore", None
    ):
      if not local_mount.startswith("/shared"):
        raise ClusterDirectorError(
            f"For Filestore storage [{storage_id}], local mount prefix must "
            "be '/shared'."
        )
    elif getattr(config, "newLustre", None) or getattr(
        config, "existingLustre", None
    ):
      if not local_mount.startswith("/scratch"):
        raise ClusterDirectorError(
            f"For Lustre storage [{storage_id}], local mount prefix must "
            "be '/scratch'."
        )
    elif getattr(config, "newBucket", None) or getattr(
        config, "existingBucket", None
    ):
      if not local_mount.startswith("/data"):
        raise ClusterDirectorError(
            f"For Bucket storage [{storage_id}], local mount prefix must "
            "be '/data'."
        )
    elif getattr(config, "existingNfs", None):
      if not (
          local_mount.startswith("/nfs") or local_mount.startswith("/shared")
      ):
        raise ClusterDirectorError(
            f"For NFS storage [{storage_id}], local mount prefix must "
            "be '/nfs' or '/shared'."
        )


def ValidateLustreFilesystemName(name: str) -> None:
  """Validates that Lustre filesystem name is between 1 and 8 characters long, lowercase letters and numbers."""
  if not re.match(r"^[a-z0-9]{1,8}$", name):
    raise ClusterDirectorError(
        f"Lustre filesystem name '{name}' is invalid. The name must be"
        " between 1 and 8 characters long and contain only lowercase letters"
        " and numbers."
    )


def ValidateBootDisk(
    machine_type: str | None, boot_disk: dict[str, Any]
) -> None:
  """Validates boot disk size and compatibility with machine type."""
  if not boot_disk:
    return
  size_gb = boot_disk.get("sizeGb")
  if size_gb is not None and size_gb <= 0:
    raise ClusterDirectorError(
        f"Boot disk sizeGb must be positive, found {size_gb}."
    )
  if not machine_type:
    return
  disk_type = boot_disk.get("type")
  if not disk_type:
    return
  if not machine_type.startswith(("n2-", "ct5p-")) and disk_type.startswith(
      "pd-"
  ):
    raise ClusterDirectorError(
        f"{disk_type} disk type cannot be used by {machine_type} machine type."
    )


def ValidateMigTargetSize(mig_id: str, target_size: int | None) -> None:
  """Validates that the managed instance group targetSize is non-negative."""
  if target_size is not None and target_size < 0:
    raise ClusterDirectorError(
        f"The target size for managed instance group '{mig_id}' must be"
        f" non-negative, found {target_size}."
    )


_EXISTING_INSTANCES_SOURCE_KEYS = (
    "project",
    "instanceGroupManager",
    "regionInstanceGroupManager",
    "reservation",
    "reservationBlock",
    "reservationSubBlock",
)


def ValidateExistingInstancesSource(
    ei_id: str, existing_instance: dict[str, Any]
) -> str:
  """Validates that an existing instances config specifies exactly one source."""
  specified_sources = [
      key
      for key in _EXISTING_INSTANCES_SOURCE_KEYS
      if existing_instance.get(key)
  ]
  if len(specified_sources) != 1:
    sources_str = ", ".join(_EXISTING_INSTANCES_SOURCE_KEYS)
    raise ClusterDirectorError(
        f"Existing instances '{ei_id}' must specify exactly one source from"
        f" [{sources_str}]."
    )
  return specified_sources[0]


def ValidateAdditionalDisk(device_name: str, disk: dict[str, Any]) -> None:
  """Validates an additional disk device name and configuration."""
  ValidateResourceID(device_name)
  sources = [k for k in ("image", "snapshot", "existingDisk") if disk.get(k)]
  if len(sources) > 1:
    raise ClusterDirectorError(
        "Only one of 'image', 'snapshot', or 'existingDisk' can be set for"
        f" additional disk '{device_name}'."
    )
  existing_disk = disk.get("existingDisk")
  if existing_disk:
    if disk.get("type") is not None or disk.get("sizeGb") is not None:
      raise ClusterDirectorError(
          "Cannot specify 'type' or 'sizeGb' when 'existingDisk' is set for"
          f" additional disk '{device_name}'."
      )
    if not re.match(r"^zones/[^/]+/disks/[^/]+$", existing_disk):
      raise ClusterDirectorError(
          f"Disk 'existingDisk' for additional disk '{device_name}' must be in"
          f" the format 'zones/ZONE/disks/DISK', found '{existing_disk}'."
      )
    return
  disk_type = disk.get("type")
  if not disk_type or "/" in disk_type:
    raise ClusterDirectorError(
        "Disk 'type' is required as a short disk type ID (e.g., 'pd-balanced')"
        " when 'existingDisk' is not set for additional disk"
        f" '{device_name}'."
    )
  size_gb = disk.get("sizeGb")
  if size_gb is None or size_gb <= 0:
    raise ClusterDirectorError(
        "Disk 'sizeGb' must be a positive integer when 'existingDisk' is not"
        f" set for additional disk '{device_name}'."
    )
  image = disk.get("image")
  if image and not re.match(r"^global/images/(family/)?[^/]+$", image):
    raise ClusterDirectorError(
        f"Disk 'image' for additional disk '{device_name}' must be in the"
        " format 'global/images/IMAGE' or 'global/images/family/FAMILY', found"
        f" '{image}'."
    )
  snapshot = disk.get("snapshot")
  if snapshot and not re.match(r"^global/snapshots/[^/]+$", snapshot):
    raise ClusterDirectorError(
        f"Disk 'snapshot' for additional disk '{device_name}' must be in the"
        f" format 'global/snapshots/SNAPSHOT', found '{snapshot}'."
    )


def ValidateSlurmNodeConfig(node_config: dict[str, Any]) -> None:
  """Validates Slurm node config."""
  if not node_config:
    return
  if node_config.get("cpuSpecList") and node_config.get("coreSpecCount"):
    raise ClusterDirectorError(
        "Cannot specify both 'cpuSpecList' and 'coreSpecCount' in Slurm node"
        " config."
    )


def ValidateControllerVersion(version: str) -> None:
  """Validates that the controller version matches the format ab.cd."""
  if not version:
    return
  if not re.match(r"^\d{2}\.\d{2}$", version):
    raise ClusterDirectorError(
        "Controller version must be in the format 'ab.cd' (e.g., '25.05'),"
        f" found '{version}'."
    )


def IsFlagSpecified(args: Any, flag: str) -> bool:
  """Returns True if flag is known and specified on args."""
  try:
    res = args.IsKnownAndSpecified(flag)
    if isinstance(res, bool):
      return res
  except Exception:  # pylint: disable=broad-exception-caught
    pass
  try:
    return bool(args.IsSpecified(flag))
  except Exception:  # pylint: disable=broad-exception-caught
    return False
