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
"""Task for updating a Rapid Cache instance."""

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log


class PatchRapidCacheTask(task.Task):
  """Updates a Rapid Cache instance."""

  def __init__(
      self,
      bucket_name,
      rapid_cache_id,
      admission_policy=None,
      ttl=None,
      is_async=True,
  ):
    """Initializes task.

    Args:
      bucket_name (str): The name of the bucket where the Rapid Cache should be
        updated.
      rapid_cache_id (str): Unique identifier for a cache instance in bucket.
      admission_policy (str|None): The cache admission policy decides for each
        cache miss, that is whether to insert the missed block or not.
      ttl (str|None): Cache entry time-to-live in seconds.
      is_async (bool): Whether to run operation asynchronously.
    """
    super(PatchRapidCacheTask, self).__init__()
    self._bucket_name = bucket_name
    self._rapid_cache_id = rapid_cache_id
    self._admission_policy = admission_policy
    self._ttl = ttl
    self._is_async = is_async
    self.parallel_processing_key = '{}/{}'.format(bucket_name, rapid_cache_id)

  def execute(self, task_status_queue=None):
    log.status.Print(
        'Updating a Rapid Cache instance of bucket gs://{} having'
        ' rapid_cache_id {}'.format(self._bucket_name, self._rapid_cache_id)
    )

    provider = storage_url.ProviderPrefix.GCS
    api_client = api_factory.get_api(provider)
    response = api_client.patch_rapid_cache(
        self._bucket_name,
        self._rapid_cache_id,
        admission_policy=self._admission_policy,
        ttl=self._ttl,
    )

    if self._is_async:
      log.status.Print(
          'Initiated the operation id: {} for updating a Rapid Cache instance'
          ' of bucket gs://{} having rapid_cache_id {}'.format(
              response.name, self._bucket_name, self._rapid_cache_id
          )
      )
    elif not response.done:
      api_client.wait_for_operation(response)

    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

  def __eq__(self, other):
    if not isinstance(other, PatchRapidCacheTask):
      return NotImplemented
    return (
        self._bucket_name == other._bucket_name
        and self._rapid_cache_id == other._rapid_cache_id
        and self._admission_policy == other._admission_policy
        and self._ttl == other._ttl
        and self._is_async == other._is_async
    )
