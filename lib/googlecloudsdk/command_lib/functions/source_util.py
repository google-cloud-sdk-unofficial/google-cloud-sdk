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
"""Version-agnostic utilities for function source code."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import random
import string
import time

from apitools.base.py import exceptions as http_exceptions
from apitools.base.py import http_wrapper
from apitools.base.py import transfer
from apitools.base.py import util as http_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.functions import exceptions
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core import transports
from googlecloudsdk.core.util import archive
from googlecloudsdk.core.util import files as file_utils
import six
from six.moves import http_client
from six.moves import range


def _GcloudIgnoreCreationPredicate(directory):
  # type: (str) -> bool
  return gcloudignore.AnyFileOrDirExists(
      directory, gcloudignore.GIT_FILES + ['node_modules']
  )


def _GetChooser(path, ignore_file):
  # type: (str, str) -> gcloudignore.FileChooser
  default_ignore_file = gcloudignore.DEFAULT_IGNORE_FILE + '\nnode_modules\n'

  return gcloudignore.GetFileChooserForDir(
      path,
      default_ignore_file=default_ignore_file,
      gcloud_ignore_creation_predicate=_GcloudIgnoreCreationPredicate,
      ignore_file=ignore_file,
  )


def _ValidateDirectoryExistsOrRaise(directory):
  # type: (str) -> None
  """Validates that the given directory exists.

  Args:
    directory: a local path to the directory provided by user.

  Returns:
    The argument provided, if found valid.
  Raises:
    SourceArgumentError: If the user provided an invalid directory.
  """
  if not os.path.exists(directory):
    raise exceptions.SourceArgumentError('Provided directory does not exist')
  if not os.path.isdir(directory):
    raise exceptions.SourceArgumentError(
        'Provided path does not point to a directory'
    )


def _ValidateUnpackedSourceSize(path, ignore_file=None):
  # type: (str, str) -> None
  """Validate size of unpacked source files."""
  chooser = _GetChooser(path, ignore_file)
  predicate = chooser.IsIncluded
  try:
    size_b = file_utils.GetTreeSizeBytes(path, predicate=predicate)
  except OSError as e:
    raise exceptions.FunctionsError(
        'Error building source archive from path [{path}]. '
        'Could not validate source files: [{error}]. '
        'Please ensure that path [{path}] contains function code or '
        'specify another directory with --source'.format(path=path, error=e)
    )
  size_limit_mb = 512
  size_limit_b = size_limit_mb * 2**20
  if size_b > size_limit_b:
    raise exceptions.OversizedDeploymentError(
        six.text_type(size_b) + 'B', six.text_type(size_limit_b) + 'B'
    )


def CreateSourcesZipFile(
    zip_dir, source_path, ignore_file=None, enforce_size_limit=False
):
  # type: (str, str, str | None, int) -> str
  """Prepare zip file with source of the function to upload.

  Args:
    zip_dir: str, directory in which zip file will be located. Name of the file
      will be `fun.zip`.
    source_path: str, directory containing the sources to be zipped.
    ignore_file: custom ignore_file name. Override .gcloudignore file to
      customize files to be skipped.
    enforce_size_limit: if set, enforces that the unpacked source size is less
      than or equal to 512 MB.

  Returns:
    Path to the zip file.
  Raises:
    FunctionsError
  """
  _ValidateDirectoryExistsOrRaise(source_path)
  if ignore_file and not os.path.exists(os.path.join(source_path, ignore_file)):
    raise exceptions.IgnoreFileNotFoundError(
        'File {0} referenced by --ignore-file does not exist.'.format(
            ignore_file
        )
    )
  if enforce_size_limit:
    _ValidateUnpackedSourceSize(source_path, ignore_file)
  zip_file_name = os.path.join(zip_dir, 'fun.zip')
  try:
    chooser = _GetChooser(source_path, ignore_file)
    predicate = chooser.IsIncluded
    archive.MakeZipFromDir(zip_file_name, source_path, predicate=predicate)
  except ValueError as e:
    raise exceptions.FunctionsError(
        'Error creating a ZIP archive with the source code '
        'for directory {0}: {1}'.format(source_path, six.text_type(e))
    )
  return zip_file_name


def _GenerateRemoteZipFileName(function_ref):
  # type: (resources.Resource) -> str
  region = function_ref.locationsId
  name = function_ref.functionsId
  suffix = ''.join(random.choice(string.ascii_lowercase) for _ in range(12))
  return '{0}-{1}-{2}.zip'.format(region, name, suffix)


def UploadToStageBucket(source_zip, function_ref, stage_bucket):
  # type: (str, resources.Resource, str) -> storage_util.ObjectReference
  """Uploads the given source ZIP file to the provided staging bucket.

  Args:
    source_zip: the source ZIP file to upload.
    function_ref: the function resource reference.
    stage_bucket: the name of GCS bucket to stage the files to.

  Returns:
    dest_object: a reference to the uploaded Cloud Storage object.
  """
  zip_file = _GenerateRemoteZipFileName(function_ref)
  bucket_ref = storage_util.BucketReference.FromArgument(stage_bucket)
  dest_object = storage_util.ObjectReference.FromBucketRef(bucket_ref, zip_file)
  try:
    storage_api.StorageClient().CopyFileToGCS(source_zip, dest_object)
  except calliope_exceptions.BadFileException:
    raise exceptions.SourceUploadError(
        'Failed to upload the function source code to the bucket {0}'.format(
            stage_bucket
        )
    )
  return dest_object


def _UploadFileToGeneratedUrlCheckResponse(base_check_response, response):
  if response.status_code == http_client.FORBIDDEN:
    raise http_exceptions.HttpForbiddenError.FromResponse(response)
  return base_check_response(response)


def _UploadFileToGeneratedUrlRetryFunc(base_retry_func, retry_args):
  if isinstance(retry_args.exc, http_exceptions.HttpForbiddenError):
    log.debug('Caught delayed permission propagation error, retrying')
    http_wrapper.RebuildHttpConnections(retry_args.http)
    time.sleep(
        http_util.CalculateWaitForRetry(
            retry_args.num_retries, max_wait=retry_args.max_retry_wait
        )
    )
  else:
    base_retry_func(retry_args)


def UploadToGeneratedUrl(source_zip, url, extra_headers=None):
  # type: (str, str, dict[str, str] | None) -> None
  """Upload the given source ZIP file to provided generated URL.

  Args:
    source_zip: the source ZIP file to upload.
    url: the signed Cloud Storage URL to upload to.
    extra_headers: extra headers to attach to the request.
  """
  extra_headers = extra_headers or {}
  upload = transfer.Upload.FromFile(source_zip, mime_type='application/zip')
  try:
    upload_request = http_wrapper.Request(
        url,
        http_method='PUT',
        headers={'content-type': 'application/zip', **extra_headers},
    )
    upload_request.body = upload.stream.read()
    response = http_wrapper.MakeRequest(
        transports.GetApitoolsTransport(),
        upload_request,
        retry_func=lambda ra: _UploadFileToGeneratedUrlRetryFunc(  # pylint: disable=g-long-lambda
            upload.retry_func, ra
        ),
        check_response_func=lambda r: _UploadFileToGeneratedUrlCheckResponse(  # pylint: disable=g-long-lambda
            http_wrapper.CheckResponse, r
        ),
        retries=upload.num_retries,
    )
  finally:
    upload.stream.close()

  if response.status_code // 100 != 2:
    raise exceptions.SourceUploadError(
        'Failed to upload the function source code to signed url: {url}. '
        'Status: [{code}:{detail}]'.format(
            url=url, code=response.status_code, detail=response.content
        )
    )
