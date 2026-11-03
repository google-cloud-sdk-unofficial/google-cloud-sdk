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
"""Task for configuring Rapid Cache policy on a GCS Managed Folder."""

from __future__ import annotations

from typing import Any

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.api_lib.storage import retry_util
from googlecloudsdk.api_lib.storage.gcs_json import metadata_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import retry


def _should_retry_precondition_error(exc_type, exc_val, exc_tb, state):
  del exc_type, exc_tb, state  # Unused.
  return (
      isinstance(exc_val, api_errors.PreconditionFailedError)
      or getattr(exc_val, 'status_code', None) == 412
  )


class EnsureManagedFoldersTask(task.Task):
  """Ensures a GCS Managed Folder Rapid Cache policy is updated for a prefix."""

  def __init__(
      self,
      bucket_name: str,
      prefix: str,
      anywhere_cache_id: str,
      enable_ingest_on_write: bool,
  ) -> None:
    """Initializes task.

    Args:
      bucket_name: The bucket name where the managed folder exists.
      prefix: Normalized prefix string to configure.
      anywhere_cache_id: The Anywhere Cache ID (zone).
      enable_ingest_on_write: True to set policy to `enabled` on the folder,
        False to set policy to `unspecified`.
    """
    super(EnsureManagedFoldersTask, self).__init__()
    self._bucket_name = bucket_name
    self._prefix = prefix
    self._anywhere_cache_id = anywhere_cache_id
    self._enable_ingest_on_write = enable_ingest_on_write
    self.parallel_processing_key = '{}/{}/{}'.format(
        self._bucket_name, self._anywhere_cache_id, self._prefix
    )

  def _raise_actionable_error(self, error: Exception) -> None:
    """Raises an actionable error naming the failed prefix and reason."""
    if self._enable_ingest_on_write:
      action_verb = 'enable'
    else:
      action_verb = 'disable'

    status_code = getattr(error, 'status_code', None) or getattr(
        getattr(error, 'payload', None), 'status_code', None
    )
    if status_code == 403:
      reason = (
          "Caller lacks 'storage.managedFolders.get',"
          " 'storage.managedFolders.create', or"
          " 'storage.managedFolders.update' IAM permissions on bucket"
          ' [gs://{}].'.format(self._bucket_name)
      )
    elif status_code == 412 or isinstance(
        error, (api_errors.PreconditionFailedError, retry.RetryException)
    ):
      reason = (
          'Managed folder metadata was concurrently modified by another'
          ' operation. Please retry.'
      )
    else:
      reason = str(error)

    raise core_exceptions.Error(
        'Failed to {} ingest-on-write for prefix [{}] on Anywhere Cache'
        ' [gs://{}/{}]. Reason: {}'.format(
            action_verb,
            self._prefix,
            self._bucket_name,
            self._anywhere_cache_id,
            reason,
        )
    )

  def _remove_stale_cache_policies(
      self, client: Any, policies: dict[str, bool]
  ) -> dict[str, bool]:
    """Returns a copy of policies keeping only active Anywhere Cache zones."""
    active_caches = client.list_anywhere_caches(self._bucket_name)
    valid_cache_ids = {self._anywhere_cache_id}
    for cache in active_caches:
      valid_cache_ids.add(cache.anywhere_cache_id)

    cleaned_policies = {}
    for cache_id, is_enabled in policies.items():
      if cache_id in valid_cache_ids:
        cleaned_policies[cache_id] = is_enabled
    return cleaned_policies

  def _update_managed_folder_policy(
      self, client: Any, existing_folder: Any | None = None
  ) -> None:
    """Updates rapid cache policy on the managed folder with 412 retry."""
    messages = getattr(client, 'messages', None) or apis.GetMessagesModule(
        'storage', 'v1'
    )
    folder_to_use = existing_folder

    def _attempt_update():
      nonlocal folder_to_use
      if folder_to_use is not None:
        folder = folder_to_use
        folder_to_use = None
      else:
        folder = client.get_managed_folder(self._bucket_name, self._prefix)

      policies = metadata_util.get_rapid_cache_policies_dict(folder)
      if (
          bool(policies.get(self._anywhere_cache_id))
          == self._enable_ingest_on_write
      ):
        return None

      policies[self._anywhere_cache_id] = self._enable_ingest_on_write
      rapid_cache_config = metadata_util.get_rapid_cache_config_from_policies(
          messages, policies
      )
      try:
        return client.update_managed_folder(
            self._bucket_name,
            self._prefix,
            rapid_cache_config=rapid_cache_config,
            if_metageneration_match=getattr(folder, 'metageneration', None),
        )
      except api_errors.GcsApiError as err:
        if getattr(err, 'status_code', None) != 400:
          raise
        cleaned_policies = self._remove_stale_cache_policies(client, policies)
        cleaned_config = metadata_util.get_rapid_cache_config_from_policies(
            messages, cleaned_policies
        )
        return client.update_managed_folder(
            self._bucket_name,
            self._prefix,
            rapid_cache_config=cleaned_config,
            if_metageneration_match=getattr(folder, 'metageneration', None),
        )

    retry_util.retryer(
        target=_attempt_update,
        should_retry_if=_should_retry_precondition_error,
    )

  def _configure_managed_folder(self, client: Any) -> None:
    """Configures the Rapid Cache policy on the managed folder."""
    try:
      existing_folder = client.get_managed_folder(
          self._bucket_name, self._prefix
      )
      self._update_managed_folder_policy(
          client, existing_folder=existing_folder
      )
    except api_errors.NotFoundError:
      if not self._enable_ingest_on_write:
        return

      log.status.Print(
          'Creating managed folder {}/{} for ingest-on-write...'.format(
              self._bucket_name, self._prefix
          )
      )
      messages = getattr(client, 'messages', None) or apis.GetMessagesModule(
          'storage', 'v1'
      )
      rapid_cache_config = metadata_util.get_rapid_cache_config_from_policies(
          messages, {self._anywhere_cache_id: True}
      )
      try:
        client.create_managed_folder(
            self._bucket_name,
            self._prefix,
            rapid_cache_config=rapid_cache_config,
        )
      except api_errors.ConflictError:
        self._update_managed_folder_policy(client)

  def execute(self, task_status_queue: Any | None = None) -> None:
    del task_status_queue  # Unused.
    if not self._prefix:
      return

    client = api_factory.get_api(storage_url.ProviderPrefix.GCS)
    try:
      self._configure_managed_folder(client)
    except (api_errors.CloudApiError, retry.RetryException) as err:
      self._raise_actionable_error(err)

  def __eq__(self, other: object) -> bool:
    if not isinstance(other, EnsureManagedFoldersTask):
      return NotImplemented
    return (
        self._bucket_name == other._bucket_name
        and self._prefix == other._prefix
        and self._anywhere_cache_id == other._anywhere_cache_id
        and self._enable_ingest_on_write == other._enable_ingest_on_write
    )
