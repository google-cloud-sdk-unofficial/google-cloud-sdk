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
"""Utilities for Anywhere Cache prefix-level ingest-on-write commands."""

from __future__ import annotations

from collections.abc import Collection, Sequence
import re

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

MAX_PREFIX_LENGTH = 1024
MAX_FOLDER_DEPTH = 15
MAX_MANAGED_FOLDERS_SCAN_LIMIT = 5000
_DISALLOWED_CHARS_PATTERN = re.compile(r'[\uFFFE\uFFFF\r\n]')
_ACME_CHALLENGE_PATH = '.well-known/acme-challenge'


def normalize_and_validate_prefix(raw_prefix: str) -> str:
  r"""Normalizes and validates a single Managed Folder prefix string.

  Enforces the 8 validation rules from go/rcmf-cli-implementation-plan §4:
  1. No leading slash ('/').
  2. No consecutive slashes ('//').
  3. No disallowed control characters ([\\uFFFE\\uFFFF\\r\\n]).
  4. Trailing slash normalization ('folder' -> 'folder/').
  5. Max length <= 1024 characters.
  6. Prohibited names: '.', '..', leading '#', or '.well-known/acme-challenge'.
  7. Max directory depth <= 15 levels.
  8. Non-empty prefix.

  Args:
    raw_prefix: Raw prefix string provided by the user.

  Returns:
    Normalized prefix string guaranteed to end with '/'.

  Raises:
    arg_parsers.ArgumentTypeError: If the prefix violates any validation rule.
  """
  if not raw_prefix or not raw_prefix.strip():
    raise arg_parsers.ArgumentTypeError(
        'Invalid prefix [{}]: prefix cannot be empty.'.format(raw_prefix)
    )

  if raw_prefix == '/':
    raise arg_parsers.ArgumentTypeError(
        'Invalid prefix [{}]: prefix cannot be root slash.'.format(raw_prefix)
    )

  if raw_prefix.startswith('/'):
    raise arg_parsers.ArgumentTypeError(
        "Invalid prefix [{}]: prefix must not start with '/'.".format(
            raw_prefix
        )
    )

  if '//' in raw_prefix:
    raise arg_parsers.ArgumentTypeError(
        "Invalid prefix [{}]: prefix must not contain consecutive slashes '//'."
        .format(raw_prefix)
    )

  if _DISALLOWED_CHARS_PATTERN.search(raw_prefix):
    raise arg_parsers.ArgumentTypeError(
        'Invalid prefix [{}]: prefix contains disallowed control characters.'
        .format(raw_prefix)
    )

  normalized = raw_prefix if raw_prefix.endswith('/') else raw_prefix + '/'

  if len(normalized.encode('utf-8')) > MAX_PREFIX_LENGTH:
    raise arg_parsers.ArgumentTypeError(
        'Invalid prefix [{}]: normalized prefix exceeds maximum length of {}'
        ' bytes (UTF-8 encoded).'.format(raw_prefix, MAX_PREFIX_LENGTH)
    )

  trimmed = normalized[:-1]

  if trimmed.startswith('#'):
    raise arg_parsers.ArgumentTypeError(
        "Invalid prefix [{}]: prefix must not start with '#'.".format(
            raw_prefix
        )
    )

  if trimmed == _ACME_CHALLENGE_PATH or trimmed.startswith(
      _ACME_CHALLENGE_PATH + '/'
  ):
    raise arg_parsers.ArgumentTypeError(
        "Invalid prefix [{}]: '{}' is a prohibited managed folder path.".format(
            raw_prefix, _ACME_CHALLENGE_PATH
        )
    )

  segments = trimmed.split('/')
  if any(seg in ('.', '..') for seg in segments):
    raise arg_parsers.ArgumentTypeError(
        "Invalid prefix [{}]: '.' and '..' path segments are prohibited."
        .format(raw_prefix)
    )

  if len(segments) > MAX_FOLDER_DEPTH:
    raise arg_parsers.ArgumentTypeError(
        'Invalid prefix [{}]: prefix depth ({}) exceeds maximum depth of {}'
        ' directory levels.'.format(raw_prefix, len(segments), MAX_FOLDER_DEPTH)
    )

  return normalized


def normalize_and_validate_prefixes(raw_prefixes: Sequence[str]) -> list[str]:
  """Normalizes, validates, and deduplicates a sequence of prefixes."""
  normalized_list = [
      normalize_and_validate_prefix(prefix) for prefix in raw_prefixes
  ]
  return list(dict.fromkeys(normalized_list))


def read_and_validate_prefixes_file(file_path: str) -> list[str]:
  """Reads prefixes from a plaintext file, ignoring blank lines and '#' comments.

  The accepted format is a plaintext file containing one prefix per line.
  Empty lines and lines beginning with '#' (comments) are ignored. Each prefix
  is validated and normalized to end with a single trailing slash.

  Args:
    file_path: Local filesystem path to the prefixes file.

  Returns:
    List of validated, normalized, and deduplicated prefix strings.
  """
  raw_prefixes = []
  with files.FileReader(file_path) as file_reader:
    for line in file_reader:
      stripped = line.strip()
      if stripped and not stripped.startswith('#'):
        raw_prefixes.append(stripped)
  return normalize_and_validate_prefixes(raw_prefixes)


def validate_ubla_for_bucket(bucket_name: str) -> None:
  """Verifies that Uniform Bucket-Level Access (UBLA) is enabled on the bucket.

  Args:
    bucket_name: Name of the GCS bucket.

  Raises:
    command_errors.Error: If UBLA is disabled on the bucket.
  """
  client = api_factory.get_api(storage_url.ProviderPrefix.GCS)
  try:
    bucket_resource = client.get_bucket(
        bucket_name, fields_scope=cloud_api.FieldsScope.NO_ACL
    )
  except api_errors.GcsApiError as e:
    status_code = getattr(e, 'status_code', None) or getattr(
        getattr(e, 'payload', None), 'status_code', None
    )
    if status_code == 403:
      log.debug(
          'Skipping pre-flight UBLA check on gs://%s due to 403 on'
          ' storage.buckets.get.',
          bucket_name,
      )
      return
    raise

  if not getattr(bucket_resource, 'uniform_bucket_level_access', False):
    raise command_errors.Error(
        'Uniform bucket-level access (UBLA) must be enabled on bucket gs://{}'
        ' to configure prefix-level ingest-on-write.'.format(bucket_name)
    )


def get_enabled_managed_folder_prefixes(
    bucket_name: str,
    cache_ids: Collection[str],
    short_circuit: bool = False,
    max_folders: int = MAX_MANAGED_FOLDERS_SCAN_LIMIT,
) -> dict[str, list[str]]:
  """Scans Managed Folders in a bucket to find IOW-enabled prefixes per cache.

  Args:
    bucket_name: Name of the GCS bucket to scan.
    cache_ids: Collection of Anywhere Cache IDs (zones) to inspect.
    short_circuit: If True, stops scanning as soon as every cache_id in
      `cache_ids` has at least one enabled prefix discovered.
    max_folders: Maximum number of managed folders to scan (default 5,000).

  Returns:
    Dictionary mapping each cache_id in `cache_ids` to a list of managed folder
    names where `rapidCacheConfig.policies[cache_id].ingestOnWrite` is
    `enabled`.
  """
  target_cache_ids = set(cache_ids)
  enabled_by_cache: dict[str, list[str]] = {cid: [] for cid in target_cache_ids}
  if not target_cache_ids:
    return enabled_by_cache

  client = api_factory.get_api(storage_url.ProviderPrefix.GCS)
  unresolved_cache_ids = set(target_cache_ids)

  for idx, folder_resource in enumerate(
      client.list_managed_folders(bucket_name)
  ):
    if idx >= max_folders:
      log.warning(
          'Managed folder scan on bucket [gs://%s] reached the %d-folder limit;'
          ' prefix-level ingest-on-write results may be incomplete.',
          bucket_name,
          max_folders,
      )
      break

    metadata = getattr(folder_resource, 'metadata', None)
    rc_config = getattr(metadata, 'rapidCacheConfig', None)
    policies = getattr(rc_config, 'policies', None)
    additional_props = getattr(policies, 'additionalProperties', None) or []

    for prop in additional_props:
      if prop.key in target_cache_ids and prop.value is not None:
        iow_val = getattr(prop.value, 'ingestOnWrite', None)
        if iow_val is not None and str(iow_val).lower() == 'enabled':
          enabled_by_cache[prop.key].append(
              folder_resource.storage_url.resource_name
          )
          unresolved_cache_ids.discard(prop.key)

    if short_circuit and not unresolved_cache_ids:
      break

  return enabled_by_cache
