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
"""Cloud Storage client that uploads packaged artifacts to a versioned prefix."""

from collections.abc import Sequence
import dataclasses

from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.packagers import models


@dataclasses.dataclass(frozen=True)
class UploadedArtifact:
  """A file that was uploaded to Cloud Storage."""

  # Object name relative to the version prefix, e.g. `dbt_gold.tar.gz`.
  relative_path: str
  gcs_uri: str
  sha256: str
  # GCS object generation, so the pipeline body can pin the exact object.
  generation: int | None = None


class GcsClient:
  """Uploads local files to Cloud Storage without overwriting objects."""

  def UploadWithPrefix(
      self,
      entries: Sequence[models.StagedFile],
      bucket: str,
      prefix: str,
  ) -> tuple[UploadedArtifact, ...]:
    """Uploads staged files under `prefix`.

    A version is never overwritten: an object that already exists with the
    same SHA-256 is skipped (so retrying a deployment is a no-op), and an
    existing object with a different SHA-256 is an error.

    Args:
      entries: Staged files and their object names relative to `prefix`.
      bucket: Destination bucket name (no `gs://`).
      prefix: Object prefix, e.g. `pipelines/<pipeline_id>/<version_id>`.

    Returns:
      One `UploadedArtifact` per entry, in input order.

    Raises:
      errors.UploadError: If an object exists with different content or an
        upload fails.
    """
    # TODO(b/567520802): Upload each entry with storage_api using
    # `ifGenerationMatch=0` and the SHA-256 stored as object metadata; on a
    # precondition failure read the existing object's metadata and skip the
    # entry when the SHA-256 matches.
    del entries, bucket, prefix
    raise errors.NotImplementedYetError(
        "GcsClient.UploadWithPrefix is not implemented yet."
    )
