# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utils for the rsync command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import fast_crc32c_util
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

import six


def get_csv_line_from_resource(resource):
  """Builds a line for files listing the contents of the source and destination.

  Args:
    resource (FileObjectResource|ObjectResource): Contains item URL and
      metadata, which can be generated from the local file in the case of
      FileObjectResource.

  Returns:
    String formatted as "URL,size,atime,mtime,uid,gid,mode,crc32c,md5".
      A missing field is represented as an empty string.
      "mtime" means "modification time", a Unix timestamp in UTC.
      "mode" is in base-eight (octal) form, e.g. "440".
  """
  url = resource.storage_url.url_string
  if isinstance(resource, resource_reference.FileObjectResource):
    size = atime = mtime = uid = gid = mode_base_eight = crc32c = md5 = None
  else:
    size = resource.size
    atime, mtime, uid, gid, mode = (
        posix_util.get_posix_attributes_from_cloud_resource(resource)
    )
    mode_base_eight = mode.base_eight_str if mode else None
    crc32c = resource.crc32c_hash
    md5 = resource.md5_hash
  line_values = [
      url,
      size,
      atime,
      mtime,
      uid,
      gid,
      mode_base_eight,
      crc32c,
      md5,
  ]
  return ','.join(['' if x is None else six.text_type(x) for x in line_values])


def parse_csv_line_to_resource(line):
  """Parses a line from files listing of rsync source and destination.

  Args:
    line (str): CSV line. See `get_csv_line_from_resource` docstring.

  Returns:
    FileObjectResource or ObjectResource containing data needed for rsync.
  """
  (
      url_string,
      size_string,
      atime_string,
      mtime_string,
      uid_string,
      gid_string,
      mode_base_eight_string,
      crc32c_string,
      md5_string,
  ) = line.split(',')
  url_object = storage_url.storage_url_from_string(url_string)
  if isinstance(url_object, storage_url.FileUrl):
    return resource_reference.FileObjectResource(url_object)
  cloud_object = resource_reference.ObjectResource(
      url_object,
      size=int(size_string),
      crc32c_hash=crc32c_string,
      md5_hash=md5_string,
      custom_fields={},
  )
  posix_util.update_custom_metadata_dict_with_posix_attributes(
      cloud_object.custom_fields,
      posix_util.PosixAttributes(
          atime=int(atime_string),
          mtime=int(mtime_string),
          uid=int(uid_string),
          gid=int(gid_string),
          mode=posix_util.PosixMode.from_base_eight_str(mode_base_eight_string),
      ),
  )
  return cloud_object


def compute_hashes_and_return_match(source_resource, destination_resource):
  """Does minimal computation to compare checksums of resources."""
  if source_resource.size != destination_resource.size:
    # Prioritizing this above other checks is an artifact from gsutil.
    # Hashes should always be different if size is different.
    return False

  check_hashes = properties.VALUES.storage.check_hashes.Get()
  if check_hashes == properties.CheckHashes.NEVER.value:
    return True

  for resource in (source_resource, destination_resource):
    if isinstance(resource, resource_reference.ObjectResource) and (
        resource.crc32c_hash is resource.md5_hash is None
    ):
      log.warning(
          'Found no hashes to validate on {}. Will not copy unless file'
          ' modification time or size difference.'.format(
              resource.storage_url.versionless_url_string
          )
      )
      # Doing the copy would be safer, but we skip for parity with gsutil.
      return True

  if isinstance(
      source_resource, resource_reference.ObjectResource
  ) and isinstance(destination_resource, resource_reference.ObjectResource):
    source_crc32c = source_resource.crc32c_hash
    destination_crc32c = destination_resource.crc32c_hash
    source_md5 = source_resource.md5_hash
    destination_md5 = destination_resource.md5_hash
    log.debug(
        'Comparing hashes for two cloud objects. CRC32C checked first.'
        ' If no comparable hash pairs, will not copy.\n'
        '{}:\n'
        '  CRC32C: {}\n'
        '  MD5: {}\n'
        '{}:\n'
        '  CRC32C: {}\n'
        '  MD5: {}\n'.format(
            source_resource.storage_url.versionless_url_string,
            source_crc32c,
            source_md5,
            destination_resource.storage_url.versionless_url_string,
            destination_crc32c,
            destination_md5,
        )
    )
    if source_crc32c is not None and destination_crc32c is not None:
      return source_crc32c == destination_crc32c
    if source_md5 is not None and destination_md5 is not None:
      return source_md5 == destination_md5
    return True

  # Local-to-local rsync not allowed, so one of these is a cloud resource.
  is_upload = isinstance(source_resource, resource_reference.FileObjectResource)
  if is_upload:
    cloud_resource = destination_resource
    local_resource = source_resource
  else:
    cloud_resource = source_resource
    local_resource = destination_resource

  if cloud_resource.crc32c_hash is not None and cloud_resource.md5_hash is None:
    # We must do a CRC32C check.
    # Let existing download flow warn that ALWAYS check may be slow.
    fast_crc32c_util.log_or_raise_crc32c_issues(warn_for_always=is_upload)
    if (
        not fast_crc32c_util.check_if_will_use_fast_crc32c(
            install_if_missing=True
        )
        and check_hashes == properties.CheckHashes.IF_FAST_ELSE_SKIP.value
    ):
      return True
    compare_crc32c = True
  elif cloud_resource.crc32c_hash is not None:
    # Prioritizing CRC32C over MD5 because google-crc32c seems significantly
    # faster than MD5 for gigabyte+ objects.
    compare_crc32c = fast_crc32c_util.check_if_will_use_fast_crc32c(
        install_if_missing=False
    )
  else:
    compare_crc32c = False

  if compare_crc32c:
    hash_algorithm = hash_util.HashAlgorithm.CRC32C
    cloud_hash = cloud_resource.crc32c_hash
  else:
    hash_algorithm = hash_util.HashAlgorithm.MD5
    cloud_hash = cloud_resource.md5_hash

  local_hash = hash_util.get_base64_hash_digest_string(
      hash_util.get_hash_from_file(
          local_resource.storage_url.object_name, hash_algorithm
      )
  )
  return cloud_hash == local_hash


def compare_metadata_and_return_copy_needed(
    source_resource,
    destination_resource,
    source_mtime,
    destination_mtime,
    compare_only_hashes=False,
    skip_if_destination_has_later_modification_time=False,
):
  """Compares metadata and returns if source should be copied to destination."""
  have_both_mtimes = source_mtime is not None and destination_mtime is not None
  if (
      skip_if_destination_has_later_modification_time
      and have_both_mtimes
      and source_mtime < destination_mtime
  ):
    return False

  # Two cloud objects should have pre-generated hashes that are more reliable
  # than mtime for seeing file differences. This ignores the unusual case where
  # cloud hashes are missing, but we still skip mtime for gsutil parity.
  skip_mtime_comparison = compare_only_hashes or (
      isinstance(source_resource, resource_reference.ObjectResource)
      and isinstance(destination_resource, resource_reference.ObjectResource)
  )
  if not skip_mtime_comparison and have_both_mtimes:
    # Ignore hashes like gsutil.
    return not (
        source_mtime == destination_mtime
        and source_resource.size == destination_resource.size
    )

  # Most expensive operation, computing hashes, saved as last resort.
  return not compute_hashes_and_return_match(
      source_resource, destination_resource
  )
