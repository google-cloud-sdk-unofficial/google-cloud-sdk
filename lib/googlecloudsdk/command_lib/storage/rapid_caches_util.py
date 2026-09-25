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
"""Utilities for Rapid Cache commands."""

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url


def validate_and_parse_rapid_cache_id(id_str: str) -> tuple[str, str]:
  """Validates and parses a composite Rapid Cache identifier.

  Args:
    id_str: The composite identifier formatted as <bucket_name>/<cache_id>.

  Returns:
    A tuple of (bucket_name, rapid_cache_id).

  Raises:
    errors.InvalidUrlError: If the identifier format is invalid (missing
      delimiter, multiple delimiters, empty bucket name, or empty cache ID).
  """
  parts = id_str.split(storage_url.CLOUD_URL_DELIMITER)
  if len(parts) != 2 or not parts[0] or not parts[1]:
    raise errors.InvalidUrlError(
        f"Invalid Rapid Cache identifier '{id_str}'. Expected format:"
        " <bucket_name>/<cache_id>"
    )
  return parts[0], parts[1]
