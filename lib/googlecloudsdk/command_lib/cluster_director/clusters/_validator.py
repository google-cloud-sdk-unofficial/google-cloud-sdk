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

from googlecloudsdk.command_lib.cluster_director.clusters import errors

ClusterDirectorError = errors.ClusterDirectorError


def ValidateFilestoreCapacity(capacity_gb: int) -> None:
  """Validates that Filestore capacity is between 1024 and 102400 GB."""
  if capacity_gb < 1024 or capacity_gb > 102400:
    raise ClusterDirectorError(
        "Filestore capacity must be between 1024 and 102400 GB, found"
        f" {capacity_gb} GB."
    )


def ValidateLustreCapacity(capacity_gb: int) -> None:
  """Validates that Lustre capacity is between 18000 and 7632000 GB."""
  if capacity_gb < 18000 or capacity_gb > 7632000:
    raise ClusterDirectorError(
        "Lustre capacity must be between 18000 and 7632000 GB, found"
        f" {capacity_gb} GB."
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
