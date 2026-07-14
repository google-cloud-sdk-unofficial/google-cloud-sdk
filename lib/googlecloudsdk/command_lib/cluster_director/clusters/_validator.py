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

