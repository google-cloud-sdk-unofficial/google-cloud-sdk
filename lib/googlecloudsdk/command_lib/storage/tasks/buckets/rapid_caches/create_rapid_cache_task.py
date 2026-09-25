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
"""Task for creating a Rapid Cache instance."""

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log


class CreateRapidCacheTask(task.Task):
  """Creates a Rapid Cache instance in a particular zone of a bucket."""

  def __init__(
      self,
      bucket_url,
      zone,
      cache_type=None,
      admission_policy=None,
      ttl=None,
      is_async=True,
  ):
    """Initializes task.

    Args:
      bucket_url (StorageUrl): The URL of the bucket where the Rapid Cache
        should be created.
      zone (str): Name of the zonal location where the Rapid Cache should be
        created.
      cache_type (str|None): The type of Rapid Cache to create.
      admission_policy (str|None): The cache admission policy decides for each
        cache miss, that is whether to insert the missed block or not.
      ttl (str|None): Cache entry time-to-live in seconds.
      is_async (bool): Whether to run operation asynchronously.
    """
    super(CreateRapidCacheTask, self).__init__()
    self._bucket_url = bucket_url
    self._zone = zone
    self._cache_type = cache_type
    self._admission_policy = admission_policy
    self._ttl = ttl
    self._is_async = is_async
    self.parallel_processing_key = '{}/{}'.format(bucket_url.bucket_name, zone)

  def execute(self, task_status_queue=None):
    log.status.Print(
        'Creating a Rapid Cache instance for bucket {} in zone {}...'.format(
            self._bucket_url, self._zone
        )
    )

    provider = self._bucket_url.scheme
    api_client = api_factory.get_api(provider)
    response = api_client.create_rapid_cache(
        self._bucket_url.bucket_name,
        self._zone,
        cache_type=self._cache_type,
        admission_policy=self._admission_policy,
        ttl=self._ttl,
    )

    if self._is_async:
      log.status.Print(
          'Initiated the operation id: {} for creating a Rapid Cache instance'
          ' for bucket {} in zone {}...'.format(
              response.name, self._bucket_url, self._zone
          )
      )
    elif not response.done:
      api_client.wait_for_operation(response)

    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

  def __eq__(self, other):
    if not isinstance(other, CreateRapidCacheTask):
      return NotImplemented
    return (
        self._bucket_url == other._bucket_url
        and self._zone == other._zone
        and self._cache_type == other._cache_type
        and self._admission_policy == other._admission_policy
        and self._ttl == other._ttl
        and self._is_async == other._is_async
    )
