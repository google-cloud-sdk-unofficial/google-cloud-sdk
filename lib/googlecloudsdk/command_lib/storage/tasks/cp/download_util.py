# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utility functions for performing download operation."""

import os
from typing import Any

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import fast_crc32c_util
from googlecloudsdk.command_lib.storage import gzip_util
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import symlink_util
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import hashing


SYMLINK_TEMPORARY_PLACEHOLDER_SUFFIX = '_sym'


def _decompress_or_rename_file(
    source_resource,
    temporary_file_path,
    final_file_path,
    do_not_decompress_flag=False,
    server_encoding=None,
):
  """Converts temporary file to final form by decompressing or renaming.

  Args:
    source_resource (ObjectResource): May contain encoding metadata.
    temporary_file_path (str): File path to unzip or rename.
    final_file_path (str): File path to write final file to.
    do_not_decompress_flag (bool): User flag that blocks decompression.
    server_encoding (str|None): Server-reported `content-encoding` of file.

  Returns:
    (bool) True if file was decompressed or renamed, and
      False if file did not exist.
  """
  if not os.path.exists(temporary_file_path):
    return False

  if gzip_util.decompress_gzip_if_necessary(source_resource,
                                            temporary_file_path,
                                            final_file_path,
                                            do_not_decompress_flag,
                                            server_encoding):
    os.remove(temporary_file_path)
  else:
    os.rename(temporary_file_path, final_file_path)
  return True


def get_digesters(
    component_number: int | None,
    resource: resource_reference.ObjectResource,
    is_streaming: bool = False,
) -> dict[hash_util.HashAlgorithm, Any]:
  """Returns digesters dictionary for download hash validation.

  Note: The digester object is not picklable. It cannot be passed between
  tasks through the task graph.

  Args:
    component_number: Used to determine if downloading a slice in a sliced
      download, which uses CRC32C for hashing.
    resource: For checking if object has known hash to validate against.
    is_streaming: Whether the download is a streaming download.

  Returns:
    Digesters dict.

  Raises:
    errors.Error: gcloud storage set to fail if performance-optimized digesters
      could not be created.
  """
  digesters = {}
  check_hashes = properties.VALUES.storage.check_hashes.Get()
  if check_hashes == properties.CheckHashes.NEVER.value:
    return digesters

  if component_number is None and resource.md5_hash:
    digesters[hash_util.HashAlgorithm.MD5] = hashing.get_md5()
  elif resource.crc32c_hash and (
      check_hashes == properties.CheckHashes.ALWAYS.value
      or fast_crc32c_util.check_if_will_use_fast_crc32c(install_if_missing=True)
  ):
    digesters[hash_util.HashAlgorithm.CRC32C] = fast_crc32c_util.get_crc32c(
        is_streaming=is_streaming
    )

  if not digesters:
    log.warning(
        'Found no hashes to validate download of object: %s. Component number:'
        ' %s. Integrity cannot be assured without hashes.',
        resource,
        component_number,
    )

  return digesters


def finalize_download(
    source_resource,
    temporary_file_path,
    final_file_path,
    do_not_decompress_flag=False,
    server_encoding=None,
    convert_symlinks=False,
):
  """Converts temporary file to final form.

  This may involve decompressing, renaming, and/or converting symlink
  placeholders to actual symlinks.

  Args:
    source_resource (ObjectResource): May contain encoding metadata.
    temporary_file_path (str): File path to unzip or rename.
    final_file_path (str): File path to write final file to.
    do_not_decompress_flag (bool): User flag that blocks decompression.
    server_encoding (str|None): Server-reported `content-encoding` of file.
    convert_symlinks (bool): Whether symlink placeholders should be converted to
      actual symlinks.

  Returns:
    (bool) True if file was decompressed, renamed, and/or converted to a
      symlink; False if file did not exist.
  """
  make_symlink = convert_symlinks and source_resource.is_symlink
  if make_symlink:
    # The decompressed/renamed content is a symlink placeholder, so store it as
    # as a temporary placeholder alongside the original temporary_file_path.
    decompress_or_rename_path = (temporary_file_path +
                                 SYMLINK_TEMPORARY_PLACEHOLDER_SUFFIX)
  else:
    decompress_or_rename_path = final_file_path

  decompress_or_rename_result = _decompress_or_rename_file(
      source_resource=source_resource,
      temporary_file_path=temporary_file_path,
      final_file_path=decompress_or_rename_path,
      do_not_decompress_flag=do_not_decompress_flag,
      server_encoding=server_encoding,
  )
  if not decompress_or_rename_result:
    return False
  if make_symlink:
    symlink_util.create_symlink_from_temporary_placeholder(
        placeholder_path=decompress_or_rename_path, symlink_path=final_file_path
    )
    os.remove(decompress_or_rename_path)
  return decompress_or_rename_result


def validate_download_hash_and_delete_corrupt_files(download_path, source_hash,
                                                    destination_hash):
  """Confirms hashes match for copied objects.

  Args:
    download_path (str): URL of object being validated.
    source_hash (str): Hash of source object.
    destination_hash (str): Hash of downloaded object.

  Raises:
    HashMismatchError: Hashes are not equal.
  """
  try:
    hash_util.validate_object_hashes_match(download_path, source_hash,
                                           destination_hash)
  except errors.HashMismatchError:
    if os.path.exists(download_path):
      os.remove(download_path)
    tracker_file_util.delete_download_tracker_files(
        storage_url.storage_url_from_string(download_path))
    raise


def return_and_report_if_nothing_to_download(cloud_resource, progress_callback):
  """Returns valid download range bool and reports progress if not."""
  if cloud_resource.size == 0:
    if progress_callback:
      progress_callback(0)
    return True
  return False


def get_crc32c_hash_for_resource(resource):
  """Returns the crc32c hash for the given resource."""

  enable_zonal_buckets_bidi_streaming = (
      properties.VALUES.storage.enable_zonal_buckets_bidi_streaming.GetBool()
  )
  if not enable_zonal_buckets_bidi_streaming:
    return resource.crc32c_hash

  try:
    # pylint: disable=g-import-not-at-top,redefined-outer-name
    from googlecloudsdk.api_lib.storage import api_factory
    from googlecloudsdk.api_lib.storage.gcs_grpc_bidi_streaming import client as gcs_grpc_bidi_streaming_client
    # pylint: enable=g-import-not-at-top,redefined-outer-name

    provider = resource.storage_url.scheme
    bucket_name = resource.storage_url.bucket_name
    api = api_factory.get_api(provider, bucket_name=bucket_name)
    if isinstance(
        api, gcs_grpc_bidi_streaming_client.GcsGrpcBidiStreamingClient
    ):
      metadata = api.get_grpc_bidi_object_metadata(
          bucket_name=resource.storage_url.bucket_name,
          object_name=resource.storage_url.resource_name,
          source_resource=resource,
          generation=resource.generation,
      )
      log.debug(
          'gRPC Bidi metadata for %s has CRC32C hash: %s',
          resource.storage_url.resource_name,
          metadata.crc32c_hash,
      )
      log.debug(
          'Source resource CRC32C hash for %s: %s',
          resource.storage_url.resource_name,
          resource.crc32c_hash,
      )
      return metadata.crc32c_hash
  except ImportError:
    # Non Zonal buckets not necesarily need to import gRPC dependent libraries.
    # For Non Zonal buckets, we will continue to use the existing flow.
    pass
  return resource.crc32c_hash
