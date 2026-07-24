# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for bucket detection and capabilities."""

import functools

from googlecloudsdk.api_lib.storage import errors as cloud_api_errors
from googlecloudsdk.api_lib.storage.gcs_json import client as gcs_json_client
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import log

_GCS_ZONAL_BUCKET_LOCATION_TYPE = 'zone'


@functools.lru_cache(maxsize=128)
def _get_is_zonal_bucket_cached(
    *, provider: storage_url.ProviderPrefix, bucket_name: str
) -> bool:
  if not bucket_name or provider != storage_url.ProviderPrefix.GCS:
    return False
  api_client = gcs_json_client.JsonClient()
  return (
      api_client.get_storage_layout(bucket_name).locationType
      == _GCS_ZONAL_BUCKET_LOCATION_TYPE
  )


def is_gcs_zonal_bucket(
    *, provider: storage_url.ProviderPrefix, bucket_name: str
) -> bool:
  """Returns true if the given bucket is a GCS zonal bucket."""
  try:
    return _get_is_zonal_bucket_cached(
        provider=provider, bucket_name=bucket_name
    )
  except cloud_api_errors.CloudApiError as e:
    status_code = getattr(e, 'status_code', None)
    if status_code in (401, 403, 404):
      log.debug(
          'Failed to get storage layout for bucket %s: %s', bucket_name, e
      )
      # If the bucket does not exist, we can assume it is not a zonal bucket.
      # If the user does not have permission to check the bucket type, we will
      # default to not using a zonal client.
      return False
    raise
