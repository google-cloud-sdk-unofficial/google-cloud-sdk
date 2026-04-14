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
"""Task for moving an object in a cloud."""

import os
import threading
from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import manifest_util
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.core import log


class MoveObjectTask(copy_util.ObjectCopyTaskWithExitHandler):
  """A task for moving an object in a cloud.

  Attributes:
    parallel_processing_key: The parallel processing key for the task.
  """

  def __init__(
      self,
      source_resource,
      destination_resource,
      api_client=None,
      print_created_message=False,
      request_config_factory_fn=None,
      user_request_args=None,
      verbose=False,
  ):
    """Initializes the MoveObjectTask.

    Args:
      source_resource (resource_reference.Resource): Must contain the full
        object path.
      destination_resource (resource_reference.Resource): Must contain the full
        object path.
      api_client (cloud_api.CloudApi|None): API client for the cloud.
      print_created_message (bool): See parent class.
      request_config_factory_fn (function|None): Function for generating
        RequestConfig.
      user_request_args (UserRequestArgs|None): See parent class
      verbose (bool): See parent class.
    """
    super(MoveObjectTask, self).__init__(
        source_resource,
        destination_resource,
        print_created_message=print_created_message,
        user_request_args=user_request_args,
        verbose=verbose,
    )

    if (
        source_resource.storage_url.scheme
        != destination_resource.storage_url.scheme
    ) or not isinstance(source_resource.storage_url, storage_url.CloudUrl):
      raise errors.InvalidUrlError(
          'MoveObjectTask takes two URLs from the same cloud provider.'
      )

    self._api_client = api_client
    self._request_config_factory_fn = (
        request_config_factory_fn or request_config_factory.get_request_config
    )
    self.parallel_processing_key = (
        self._destination_resource.storage_url.url_string
    )

  def execute(self, task_status_queue=None):
    api_client = self._api_client or api_factory.get_api(
        self._source_resource.storage_url.scheme
    )

    if copy_util.check_for_cloud_clobber(
        self._user_request_args, api_client, self._destination_resource
    ):
      no_clobber_message = copy_util.get_no_clobber_message(
          self._destination_resource.storage_url
      )
      log.status.Print(no_clobber_message)
      if self._send_manifest_messages:
        manifest_util.send_skip_message(
            task_status_queue,
            self._source_resource,
            self._destination_resource,
            no_clobber_message,
        )
      return None

    progress_callback = progress_callbacks.FilesAndBytesProgressCallback(
        status_queue=task_status_queue,
        offset=0,
        length=self._source_resource.size,
        source_url=self._source_resource.storage_url,
        destination_url=self._destination_resource.storage_url,
        operation_name=task_status.OperationName.INTRA_CLOUD_COPYING,
        process_id=os.getpid(),
        thread_id=threading.get_ident(),
    )

    request_config = self._request_config_factory_fn(
        url=self._destination_resource.storage_url,
        user_request_args=self._user_request_args,
    )

    result_resource = api_client.move_object(
        self._source_resource.storage_url,
        destination_url=self._destination_resource.storage_url,
        request_config=request_config,
        progress_callback=progress_callback,
    )

    self._print_created_message_if_requested(result_resource)
    if self._send_manifest_messages:
      manifest_util.send_success_message(
          task_status_queue,
          self._source_resource,
          self._destination_resource,
          md5_hash=result_resource.md5_hash,
      )

    return task.Output(additional_task_iterators=None, messages=None)

  def __eq__(self, other):
    if not isinstance(other, MoveObjectTask):
      return NotImplemented
    return (
        self._source_resource == other._source_resource
        and self._destination_resource == other._destination_resource
        and self._api_client == other._api_client
        and self._print_created_message == other._print_created_message
        and self._request_config_factory_fn == other._request_config_factory_fn
        and self._user_request_args == other._user_request_args
        and self._verbose == other._verbose
    )
