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
"""Cloud Storage client for uploading packaged pipeline artifacts."""

from collections.abc import Sequence
import dataclasses
import http
import mimetypes
import pathlib
from typing import Any

from apitools.base.py import exceptions as api_exceptions
from apitools.base.py import transfer
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.packagers import models
from googlecloudsdk.command_lib.util import crc32c
from googlecloudsdk.core import log

_READ_CHUNK_SIZE = 64 * 1024


@dataclasses.dataclass(frozen=True)
class UploadedArtifact:
  """Metadata for an artifact uploaded to Cloud Storage.

  Attributes:
    relative_path: Object name relative to the version prefix, e.g.
      `dbt_gold.tar.gz`.
    gcs_uri: Full `gs://<bucket>/<object>` URI of the uploaded artifact.
    sha256: Lowercase hex SHA-256 digest of the artifact contents.
    crc32c: Base64-encoded CRC32C checksum from Cloud Storage, or None if unset.
  """

  relative_path: str
  gcs_uri: str
  sha256: str
  crc32c: str | None = None


def BuildVersionedArtifactPrefix(
    pipeline_id: str, version_id: str, path_prefix: str = ""
) -> str:
  """Returns the GCS object prefix for `(pipeline_id, version_id)`.

  Args:
    pipeline_id: The pipeline identifier.
    version_id: The deployment version identifier.
    path_prefix: Optional leading object prefix from `deployment.yaml`.

  Returns:
    The joined GCS object prefix without leading or trailing slashes.
  """
  prefix_segments = (
      path_prefix.strip("/"),
      "pipelines",
      pipeline_id,
      version_id,
  )
  return "/".join(segment for segment in prefix_segments if segment)


class GcsClient:
  """Uploads staged artifacts to Cloud Storage without overwriting objects."""

  def __init__(self, storage_client: storage_api.StorageClient | None = None):
    """Initializes the instance.

    Args:
      storage_client: Optional Cloud Storage API client; created lazily using
        default credentials if None.
    """
    self._storage_client = storage_client

  def UploadWithPrefix(
      self,
      entries: Sequence[models.StagedFile],
      bucket: str,
      prefix: str,
  ) -> tuple[UploadedArtifact, ...]:
    """Uploads staged files under `prefix`, skipping identical existing objects.

    Args:
      entries: Staged files and their object names relative to `prefix`.
      bucket: Destination bucket name (with or without `gs://`).
      prefix: Object prefix, e.g. `pipelines/<pipeline_id>/<version_id>`.

    Returns:
      One `UploadedArtifact` per entry, in input order.

    Raises:
      errors.UploadError: If the destination URI is invalid, an existing object
        has different content, or an upload fails.
    """
    bucket_name = bucket.strip().removeprefix("gs://").strip("/")
    clean_prefix = prefix.strip("/")
    uploaded = []
    for entry in entries:
      relative_path = entry.relative_path.lstrip("/")
      object_name = (
          f"{clean_prefix}/{relative_path}" if clean_prefix else relative_path
      )
      object_ref = _ParseGcsUri(f"gs://{bucket_name}/{object_name}")
      gcs_object = self._UploadIfAbsent(entry.local_path, object_ref)
      uploaded.append(
          UploadedArtifact(
              relative_path=entry.relative_path,
              gcs_uri=object_ref.ToUrl(),
              sha256=entry.sha256,
              crc32c=gcs_object.crc32c,
          )
      )
    return tuple(uploaded)

  def _UploadIfAbsent(
      self,
      local_path: pathlib.Path,
      object_ref: storage_util.ObjectReference,
  ) -> Any:
    """Uploads `local_path` with `ifGenerationMatch=0` or checks existing."""
    gcs_uri = object_ref.ToUrl()
    request = _BuildCreateOnlyObjectInsertRequest(
        self._storage.messages, object_ref
    )
    upload = _OpenFileForUpload(local_path)
    log.info("Uploading '%s' to %s", local_path, gcs_uri)
    try:
      return self._storage.client.objects.Insert(request, upload=upload)
    except api_exceptions.HttpError as e:
      if e.status_code != http.HTTPStatus.PRECONDITION_FAILED:
        raise errors.UploadError(
            f"Failed to upload '{local_path}' to {gcs_uri}: {e}"
        ) from e
    finally:
      upload.stream.close()

    return self._VerifyExistingObject(local_path, object_ref)

  @property
  def _storage(self) -> storage_api.StorageClient:
    if self._storage_client is None:
      self._storage_client = storage_api.StorageClient()
    return self._storage_client

  def _VerifyExistingObject(
      self,
      local_path: pathlib.Path,
      object_ref: storage_util.ObjectReference,
  ) -> Any:
    """Verifies an existing object at `object_ref` has the same CRC32C."""
    gcs_uri = object_ref.ToUrl()
    expected_crc32c = _ComputeFileCrc32c(local_path)
    try:
      existing = self._storage.GetObject(object_ref)
    except api_exceptions.HttpError as e:
      raise errors.UploadError(
          f"{gcs_uri} already exists and could not be read: {e}"
      ) from e
    if existing.crc32c != expected_crc32c:
      raise errors.UploadError(
          f"{gcs_uri} already exists with different content (crc32c"
          f" {existing.crc32c} on Cloud Storage, {expected_crc32c} locally);"
          " deploy a new version instead."
      )
    log.info("Skipping %s: it already exists with the same content.", gcs_uri)
    return existing


def _ParseGcsUri(gcs_uri: str) -> storage_util.ObjectReference:
  """Parses and validates a `gs://<bucket>/<object>` URI."""
  try:
    return storage_util.ObjectReference.FromUrl(gcs_uri.strip())
  except (storage_util.InvalidNameError, ValueError) as e:
    raise errors.UploadError(
        f"Invalid Cloud Storage URI '{gcs_uri}': must be of the form"
        " 'gs://<bucket>/<object>'."
    ) from e


def _BuildCreateOnlyObjectInsertRequest(
    messages: Any,
    object_ref: storage_util.ObjectReference,
) -> Any:
  """Builds a create-only `StorageObjectsInsertRequest` for `object_ref`."""
  return messages.StorageObjectsInsertRequest(
      bucket=object_ref.bucket,
      name=object_ref.name,
      object=messages.Object(name=object_ref.name),
      ifGenerationMatch=0,
  )


def _OpenFileForUpload(local_path: pathlib.Path) -> transfer.Upload:
  """Opens `local_path` as a streaming `transfer.Upload`."""
  mime_type, _ = mimetypes.guess_type(local_path.name)
  try:
    return transfer.Upload.FromFile(
        str(local_path),
        mime_type=mime_type or "application/octet-stream",
    )
  except (OSError, api_exceptions.Error) as e:
    raise errors.UploadError(f"Failed to read '{local_path}': {e}") from e


def _ComputeFileCrc32c(local_path: pathlib.Path) -> str:
  """Returns the base64-encoded CRC32C checksum of `local_path`."""
  hasher = crc32c.get_crc32c()
  try:
    with local_path.open("rb") as stream:
      while chunk := stream.read(_READ_CHUNK_SIZE):
        hasher.update(chunk)
  except OSError as e:
    raise errors.UploadError(f"Failed to read '{local_path}': {e}") from e
  return crc32c.get_hash(hasher)
