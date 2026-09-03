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
"""Makes the dbt artifacts named by ``--artifacts-path`` readable locally.

``--artifacts-path`` accepts a local directory or a Cloud Storage folder. The
transform reads the artifacts with plain filesystem calls, so a Cloud Storage
folder is downloaded into a local directory first and everything downstream
reads that copy.
"""

from __future__ import annotations

import os

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.dataplex.dbt import transform as dbt_transform
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

# Declared here rather than at the parser, so the module that reports errors
# against the flag is the module that names it.
ARTIFACTS_PATH_FLAG = '--artifacts-path'

# --artifacts-path may name the dbt project root rather than the folder holding
# the artifacts, since dbt writes them into `target/` underneath it. Both are
# looked in, which is what a local path already does.
_NESTED_FOLDER = 'target/'


def IsCloudStoragePath(artifacts_path: str) -> bool:  # pylint: disable=invalid-name
  """Returns whether --artifacts-path names a Cloud Storage folder."""
  return artifacts_path.startswith(storage_util.GSUTIL_BUCKET_PREFIX)


def Download(  # pylint: disable=invalid-name
    artifacts_path: str, download_dir: str
) -> str:
  """Downloads the dbt artifacts held in a Cloud Storage folder.

  Args:
    artifacts_path: a ``gs://bucket/folder`` naming either the dbt project root
      or the folder holding the artifacts.
    download_dir: the local directory to download into; created if absent.

  Returns:
    ``download_dir``, holding manifest.json plus whichever optional artifacts
    were present in the folder.

  Raises:
    calliope_exceptions.InvalidArgumentException: if artifacts_path is not a
      valid Cloud Storage path, holds no manifest.json, or names an object the
      caller may not read.
  """
  folder = artifacts_path.rstrip('/') + '/'
  # Parsing the manifest URI validates the bucket and object name in one go, so
  # a malformed path is reported against what the caller actually typed rather
  # than against a URI this module derived from it.
  try:
    storage_util.ObjectReference.FromUrl(folder + dbt_transform.MANIFEST_FILE)
  except ValueError as e:
    raise calliope_exceptions.InvalidArgumentException(
        ARTIFACTS_PATH_FLAG,
        '[{0}] is not a valid Cloud Storage path; expected '
        'gs://BUCKET/FOLDER.'.format(artifacts_path),
    ) from e

  client = storage_api.StorageClient()
  folder = _FolderHoldingManifest(client, folder)
  log.status.Print(
      'Downloading dbt artifacts from [{0}] to a local temporary directory'
      ' ...'.format(folder)
  )
  files.MakeDir(download_dir)
  _Copy(client, folder, dbt_transform.MANIFEST_FILE, download_dir)
  for name in dbt_transform.OPTIONAL_ARTIFACTS:
    obj_ref = storage_util.ObjectReference.FromUrl(folder + name)
    if _Exists(client, obj_ref, required=False):
      _Copy(client, folder, name, download_dir)
  return download_dir


def _FolderHoldingManifest(
    client: storage_api.StorageClient, folder: str
) -> str:
  """Returns whichever of ``folder`` / its ``target/`` holds the manifest."""
  candidates = (folder, folder + _NESTED_FOLDER)
  for candidate in candidates:
    uri = candidate + dbt_transform.MANIFEST_FILE
    if _Exists(client, storage_util.ObjectReference.FromUrl(uri)):
      return candidate
    log.info('No dbt manifest at [%s].', uri)
  raise calliope_exceptions.InvalidArgumentException(
      ARTIFACTS_PATH_FLAG,
      'No [{0}] found at [{1}] or [{2}]. Point {3} at a dbt project root or at'
      ' the folder holding its artifacts.'.format(
          dbt_transform.MANIFEST_FILE,
          candidates[0],
          candidates[1],
          ARTIFACTS_PATH_FLAG,
      ),
  )


def _Exists(
    client: storage_api.StorageClient,
    obj_ref: storage_util.ObjectReference,
    *,
    required: bool = True,
) -> bool:
  """Returns whether the object is there.

  Existence is probed with a metadata read rather than an unconditional
  download: ``CopyFileFromGCS`` creates the local file before it issues the
  request and reports every failure as the same error, so a missing optional
  artifact would leave an empty file behind and a permission failure would be
  indistinguishable from an absent object.

  Args:
    client: the Cloud Storage client.
    obj_ref: the object to probe.
    required: whether the run needs this artifact. An unreadable optional
      artifact is skipped with a warning, matching what a local --artifacts-path
      does with one it cannot read; an unreadable required one is fatal.

  Returns:
    True if the object exists, False if it does not.

  Raises:
    calliope_exceptions.InvalidArgumentException: if the caller may not read a
      required object, since that is not an answer to whether it exists.
  """
  try:
    client.GetObject(obj_ref)
  except apitools_exceptions.HttpNotFoundError:
    log.debug('dbt artifact [%s] is absent.', obj_ref.ToUrl())
    return False
  except apitools_exceptions.HttpForbiddenError as e:
    if not required:
      log.warning(
          'Access denied reading optional dbt artifact [{0}]; ignoring it. '
          'Some metadata may be missing.'.format(obj_ref.ToUrl())
      )
      return False
    raise calliope_exceptions.InvalidArgumentException(
        ARTIFACTS_PATH_FLAG,
        'Access denied reading [{0}]. Reading dbt artifacts from Cloud Storage'
        ' needs the storage.objects.get permission on them (e.g.'
        ' roles/storage.objectViewer).'.format(obj_ref.ToUrl()),
    ) from e
  return True


def _Copy(
    client: storage_api.StorageClient,
    folder: str,
    name: str,
    download_dir: str,
) -> None:
  """Downloads ``folder + name`` into ``download_dir`` under its own name."""
  client.CopyFileFromGCS(
      storage_util.ObjectReference.FromUrl(folder + name),
      os.path.join(download_dir, name),
  )
