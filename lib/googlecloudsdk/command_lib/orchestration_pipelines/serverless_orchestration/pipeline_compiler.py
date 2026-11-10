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
"""Compiles a loaded pipeline and its uploaded artifacts into an API body."""

from collections.abc import Mapping, Sequence
import dataclasses
from typing import Any

from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import pipeline_loader
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.clients import gcs_client
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.packagers import dbt


@dataclasses.dataclass(frozen=True)
class CompiledPipeline:
  """Compiled Orchestration API `Pipeline` resource and request payload.

  Attributes:
    parent: Parent location resource name (`projects/*/locations/*`).
    pipeline_id: Pipeline identifier under `parent`.
    body: `Pipeline` resource fields sent in the create or update request.
    version_id: Deployment version identifier.
  """

  parent: str
  pipeline_id: str
  body: Mapping[str, Any]
  version_id: str

  @property
  def name(self) -> str:
    """Full resource name of the pipeline."""
    return f"{self.parent}/pipelines/{self.pipeline_id}"


def BuildPipelineResourceName(
    loaded_pipeline: pipeline_loader.LoadedPipeline,
) -> str:
  """Returns the `projects/*/locations/*/pipelines/*` name of the pipeline.

  Args:
    loaded_pipeline: The validated pipeline and environment model.

  Returns:
    The full resource name of the pipeline being deployed.
  """
  return (
      f"{_BuildParentResourceName(loaded_pipeline)}"
      f"/pipelines/{loaded_pipeline.pipeline_id}"
  )


def CompilePipeline(
    loaded_pipeline: pipeline_loader.LoadedPipeline,
    uploaded_artifacts_by_action: Mapping[
        str, Sequence[gcs_client.UploadedArtifact]
    ],
    version_id: str,
) -> CompiledPipeline:
  """Builds the Orchestration API `Pipeline` payload for `loaded_pipeline`.

  Every dbt action becomes a dbt data model of a `DataPipeline`, which runs the
  uploaded archive of the action on the Google-managed dbt runtime as the
  service account of the pipeline. Runs write their output artifacts to the
  `outputs` directory next to the uploaded versions of the pipeline.

  Args:
    loaded_pipeline: The validated pipeline and environment model.
    uploaded_artifacts_by_action: Uploaded GCS artifacts keyed by action name.
    version_id: The deployment version identifier. It is not part of the body
      because the Orchestration service rejects `Pipeline.version_id`.

  Returns:
    The compiled `Pipeline` resource and identity.

  Raises:
    errors.PipelineCompileError: If an action does not have exactly one
      uploaded archive, or Cloud Storage reported no CRC32C checksum for it.
  """
  return CompiledPipeline(
      parent=_BuildParentResourceName(loaded_pipeline),
      pipeline_id=loaded_pipeline.pipeline_id,
      body=_BuildPipelineBody(loaded_pipeline, uploaded_artifacts_by_action),
      version_id=version_id,
  )


def _BuildParentResourceName(
    loaded_pipeline: pipeline_loader.LoadedPipeline,
) -> str:
  """Returns the `projects/*/locations/*` parent of the pipeline."""
  return (
      f"projects/{loaded_pipeline.project}/locations/{loaded_pipeline.location}"
  )


def _BuildPipelineBody(
    loaded_pipeline: pipeline_loader.LoadedPipeline,
    uploaded_artifacts_by_action: Mapping[
        str, Sequence[gcs_client.UploadedArtifact]
    ],
) -> dict[str, Any]:
  """Returns the `Pipeline` fields that the pipeline YAML defines."""
  return {
      "spec": {
          "data_pipeline": _BuildDataPipeline(
              loaded_pipeline.actions, uploaded_artifacts_by_action
          ),
      },
      "execution_identity": _BuildExecutionIdentity(loaded_pipeline),
      "output_artifact_storage": _BuildOutputArtifactStorage(loaded_pipeline),
  }


def _BuildDataPipeline(
    actions: Sequence[pipeline_loader.DbtAction],
    uploaded_artifacts_by_action: Mapping[
        str, Sequence[gcs_client.UploadedArtifact]
    ],
) -> dict[str, Any]:
  """Returns a `DataPipeline` with one dbt data model per action."""
  return {
      "data_models": [
          _BuildDbtDataModel(
              action,
              _GetExecutionArchive(action.name, uploaded_artifacts_by_action),
          )
          for action in actions
      ],
  }


def _BuildDbtDataModel(
    action: pipeline_loader.DbtAction,
    execution_archive: gcs_client.UploadedArtifact,
) -> dict[str, Any]:
  """Returns the `DataModel` that runs `action` from `execution_archive`."""
  return {
      "id": action.name,
      "dbt": {
          # The packager stores the dbt project under this top-level directory
          # of the archive.
          "source_path": dbt.ARCHIVE_ROOT_DIR,
          "execution_archive": {
              "gcs": {
                  "uri": execution_archive.gcs_uri,
                  "crc32c": execution_archive.crc32c,
              },
          },
          "managed_runtime": {"dbt_version": action.dbt_version},
      },
  }


def _GetExecutionArchive(
    action_name: str,
    uploaded_artifacts_by_action: Mapping[
        str, Sequence[gcs_client.UploadedArtifact]
    ],
) -> gcs_client.UploadedArtifact:
  """Returns the single archive uploaded for `action_name`.

  Args:
    action_name: Name of the dbt action.
    uploaded_artifacts_by_action: Uploaded GCS artifacts keyed by action name.

  Returns:
    The uploaded archive of the action, which has a CRC32C checksum.

  Raises:
    errors.PipelineCompileError: If the action does not have exactly one
      uploaded archive, or Cloud Storage reported no CRC32C checksum for it.
  """
  uploaded_artifacts = uploaded_artifacts_by_action.get(action_name, ())
  if len(uploaded_artifacts) != 1:
    raise errors.PipelineCompileError(
        f"Expected exactly one uploaded archive for action '{action_name}',"
        f" got {len(uploaded_artifacts)}."
    )
  execution_archive = uploaded_artifacts[0]
  # The Orchestration service requires the checksum to verify the archive.
  if not execution_archive.crc32c:
    raise errors.PipelineCompileError(
        "Cloud Storage reported no CRC32C checksum for"
        f" {execution_archive.gcs_uri}."
    )
  return execution_archive


def _BuildExecutionIdentity(
    loaded_pipeline: pipeline_loader.LoadedPipeline,
) -> dict[str, Any]:
  """Returns the `ExecutionIdentity` that runs of the pipeline use."""
  return {"service_account": {"email": loaded_pipeline.service_account}}


def _BuildOutputArtifactStorage(
    loaded_pipeline: pipeline_loader.LoadedPipeline,
) -> dict[str, Any]:
  """Returns the `ArtifactStorage` where runs of the pipeline write outputs."""
  output_prefix = gcs_client.BuildOutputArtifactPrefix(
      loaded_pipeline.pipeline_id, loaded_pipeline.artifact_path_prefix
  )
  # No trailing slash: the service appends subdirectories such as `/compile`
  # to the URI.
  output_uri = f"gs://{loaded_pipeline.artifact_bucket}/{output_prefix}"
  return {"gcs": {"uri": output_uri}}
