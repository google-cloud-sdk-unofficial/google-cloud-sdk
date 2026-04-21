# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Preferred method of generating a copy task."""


from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.cp import copy_folder_task
from googlecloudsdk.command_lib.storage.tasks.cp import copy_managed_folder_task
from googlecloudsdk.command_lib.storage.tasks.cp import daisy_chain_copy_task
from googlecloudsdk.command_lib.storage.tasks.cp import file_download_task
from googlecloudsdk.command_lib.storage.tasks.cp import file_upload_task
from googlecloudsdk.command_lib.storage.tasks.cp import intra_cloud_copy_task
from googlecloudsdk.command_lib.storage.tasks.cp import move_object_task
from googlecloudsdk.command_lib.storage.tasks.cp import parallel_composite_upload_util
from googlecloudsdk.command_lib.storage.tasks.cp import streaming_download_task
from googlecloudsdk.command_lib.storage.tasks.cp import streaming_upload_task
from googlecloudsdk.core import properties


def _should_use_move_object_task(
    source_resource,
    destination_resource,
    delete_source,
    posix_to_set,
    user_request_args,
):
  """Returns True if MoveObjectTask should be used for intra-cloud moves."""
  if not properties.VALUES.storage.use_move_object_api.GetBool():
    # TODO: b/331725321 - Remove this check post implementation.
    return False

  if not delete_source or posix_to_set:
    return False

  source_url = source_resource.storage_url
  destination_url = destination_resource.storage_url
  if (
      source_url.scheme != storage_url.ProviderPrefix.GCS
      or destination_url.scheme != storage_url.ProviderPrefix.GCS
      or source_url.bucket_name != destination_url.bucket_name
      or not isinstance(source_resource, resource_reference.ObjectResource)
  ):
    return False

  # MoveObjects doesn't support overriding encryption keys.
  if encryption_util.get_encryption_key():
    return False

  # Move object is only supported for live objects.
  if source_url.generation:
    return False

  if not user_request_args:
    return True
  if (
      user_request_args.gzip_settings
      or user_request_args.manifest_path
      or user_request_args.predefined_acl_string
      or user_request_args.preserve_posix
  ):
    return False

  resource_args = user_request_args.resource_args
  if not resource_args:
    return True

  # If preserve_acl is set to False, we should not use MoveObjectTask.
  # MoveObjectTask will preserve ACLs by default.
  preserve_acl = getattr(resource_args, 'preserve_acl', None)
  if preserve_acl is not None and not preserve_acl:
    return False

  # If any object resource_args are set, MoveObjectTask is not supported.
  for field in [
      'acl_file_path',
      'acl_grants_to_add',
      'acl_grants_to_remove',
      'cache_control',
      'content_disposition',
      'content_encoding',
      'content_language',
      'content_type',
      'custom_contexts_to_set',
      'custom_contexts_to_remove',
      'custom_contexts_to_update',
      'custom_fields_to_set',
      'custom_fields_to_remove',
      'custom_fields_to_update',
      'custom_time',
      'event_based_hold',
      'md5_hash',
      'retain_until',
      'retention_mode',
      'storage_class',
      'temporary_hold',
  ]:
    val = getattr(resource_args, field, None)
    if val:
      return False

  return True


def get_copy_task(
    source_resource,
    destination_resource,
    delete_source=False,
    do_not_decompress=False,
    fetch_source_fields_scope=None,
    force_daisy_chain=False,
    posix_to_set=None,
    print_created_message=False,
    print_source_version=False,
    shared_stream=None,
    user_request_args=None,
    verbose=False,
):
  """Factory method that returns the correct copy task for the arguments.

  Args:
    source_resource (resource_reference.Resource): Reference to file to copy.
    destination_resource (resource_reference.Resource): Reference to destination
      to copy file to.
    delete_source (bool): If copy completes successfully, delete the source
      object afterwards.
    do_not_decompress (bool): Prevents automatically decompressing downloaded
      gzips.
    fetch_source_fields_scope (FieldsScope|None): If present, refetch
      source_resource, populated with metadata determined by this FieldsScope.
      Useful for lazy or parallelized GET calls. Currently only implemented for
      intra-cloud copies and daisy chain copies.
    force_daisy_chain (bool): If True, yields daisy chain copy tasks in place of
      intra-cloud copy tasks.
    posix_to_set (PosixAttributes|None): Triggers setting POSIX on result of
      copy and avoids re-parsing POSIX info.
    print_created_message (bool): Print the versioned URL of each successfully
      copied object.
    print_source_version (bool): Print source object version in status message
      enabled by the `verbose` kwarg.
    shared_stream (stream): Multiple tasks may reuse this read or write stream.
    user_request_args (UserRequestArgs|None): Values for RequestConfig.
    verbose (bool): Print a "copying" status message on task initialization.

  Returns:
    Task object that can be executed to perform a copy.

  Raises:
    NotImplementedError: Cross-cloud copy.
    Error: Local filesystem copy.
  """
  source_url = source_resource.storage_url
  destination_url = destination_resource.storage_url

  if (isinstance(source_url, storage_url.FileUrl)
      and isinstance(destination_url, storage_url.FileUrl)):
    raise errors.Error(
        'Local copies not supported. Gcloud command-line tool is'
        ' meant for cloud operations. Received copy from {} to {}'.format(
            source_url, destination_url
        )
    )

  if (isinstance(source_url, storage_url.CloudUrl)
      and isinstance(destination_url, storage_url.FileUrl)):
    if destination_url.is_stream:
      return streaming_download_task.StreamingDownloadTask(
          source_resource,
          destination_resource,
          shared_stream,
          print_created_message=print_created_message,
          print_source_version=print_source_version,
          user_request_args=user_request_args,
          verbose=verbose,
      )

    return file_download_task.FileDownloadTask(
        source_resource,
        destination_resource,
        delete_source=delete_source,
        do_not_decompress=do_not_decompress,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        print_source_version=print_source_version,
        system_posix_data=posix_util.run_if_setting_posix(
            posix_to_set, user_request_args, posix_util.get_system_posix_data
        ),
        user_request_args=user_request_args,
        verbose=verbose,
    )

  if (isinstance(source_url, storage_url.FileUrl)
      and isinstance(destination_url, storage_url.CloudUrl)):
    if source_url.is_stream:
      return streaming_upload_task.StreamingUploadTask(
          source_resource,
          destination_resource,
          posix_to_set=posix_to_set,
          print_created_message=print_created_message,
          print_source_version=print_source_version,
          user_request_args=user_request_args,
          verbose=verbose,
      )
    else:
      is_composite_upload_eligible = (
          parallel_composite_upload_util.is_composite_upload_eligible(
              source_resource, destination_resource, user_request_args))
      return file_upload_task.FileUploadTask(
          source_resource,
          destination_resource,
          delete_source=delete_source,
          is_composite_upload_eligible=is_composite_upload_eligible,
          posix_to_set=posix_to_set,
          print_created_message=print_created_message,
          print_source_version=print_source_version,
          user_request_args=user_request_args,
          verbose=verbose,
      )

  if (isinstance(source_url, storage_url.CloudUrl)
      and isinstance(destination_url, storage_url.CloudUrl)):
    different_providers = source_url.scheme != destination_url.scheme
    if (different_providers and user_request_args and
        user_request_args.resource_args and
        user_request_args.resource_args.preserve_acl):
      raise errors.Error(
          'Cannot preserve ACLs while copying between cloud providers.'
      )

    # If the source_resource is a folder and other conditions for rename_folders
    # are met, we need not invoke the CopyManagedFolderTask
    # as the CopyFolderTask would take care of it automaticlally.
    is_folders_use_case = (
        isinstance(source_resource, resource_reference.FolderResource)
        and not different_providers
    )
    if (
        is_folders_use_case
        and delete_source
        and not force_daisy_chain
        and source_resource.bucket
        == destination_resource.storage_url.bucket_name
    ):
      return copy_folder_task.RenameFolderTask(
          source_resource,
          destination_resource,
          print_created_message=print_created_message,
          user_request_args=user_request_args,
          verbose=verbose,
      )
    elif is_folders_use_case:
      return copy_folder_task.CopyFolderTask(
          source_resource,
          destination_resource,
          print_created_message=print_created_message,
          user_request_args=user_request_args,
          verbose=verbose,
      )
    elif isinstance(source_resource, resource_reference.ManagedFolderResource):
      return copy_managed_folder_task.CopyManagedFolderTask(
          source_resource,
          destination_resource,
          print_created_message=print_created_message,
          user_request_args=user_request_args,
          verbose=verbose,
      )
    if different_providers or force_daisy_chain:
      return daisy_chain_copy_task.DaisyChainCopyTask(
          source_resource,
          destination_resource,
          delete_source=delete_source,
          posix_to_set=posix_to_set,
          print_created_message=print_created_message,
          print_source_version=print_source_version,
          user_request_args=user_request_args,
          verbose=verbose,
          fetch_source_fields_scope=fetch_source_fields_scope,
      )

    if _should_use_move_object_task(
        source_resource,
        destination_resource,
        delete_source,
        posix_to_set,
        user_request_args,
    ):
      return move_object_task.MoveObjectTask(
          source_resource,
          destination_resource,
          print_created_message=print_created_message,
          user_request_args=user_request_args,
          verbose=verbose,
      )

    return intra_cloud_copy_task.IntraCloudCopyTask(
        source_resource,
        destination_resource,
        delete_source=delete_source,
        fetch_source_fields_scope=fetch_source_fields_scope,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        print_source_version=print_source_version,
        user_request_args=user_request_args,
        verbose=verbose,
    )
