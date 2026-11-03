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
"""Deployer for Serverless Orchestration API pipelines."""

import argparse
from collections.abc import Sequence
import dataclasses
import datetime
import pathlib
from typing import Any

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import pipeline_loader
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.clients import gcs_client
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.packagers import dbt
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.packagers import models
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


@dataclasses.dataclass(frozen=True)
class DeployResult:
  """Result of deploying a Serverless Orchestration pipeline."""

  pipeline_name: str
  version_id: str
  artifacts: tuple[str, ...]
  operation: str | None
  status: str


def IsServerlessOrchestrationDeployment(args: argparse.Namespace) -> bool:
  """Returns True if the configured pipelines use `runner: orchestration_service`.

  Returns False when a YAML file is missing or invalid so the Cloud Composer
  flow reports the error.

  Args:
    args: The parsed command-line arguments.

  Returns:
    True if the configured pipelines use `runner: orchestration_service`.

  Raises:
    errors.PipelineLoadError: If `deployment.yaml` mixes `orchestration_service`
      with another `runner` field, or if `deployment.yaml` is absent and
      `./pipeline.yaml` is malformed.
  """
  try:
    runner_fields = _GetRunnerFieldsFromPipelineFiles(args.environment)
  except errors.PipelineLoadError as e:
    if _HasStandaloneDefaultPipelineFile():
      raise
    log.debug(
        "Routing deployment to Cloud Composer after pipeline check failed: %s",
        e,
    )
    return False
  _VerifyAllPipelinesShareSameRunnerField(runner_fields)
  return pipeline_loader.ORCHESTRATION_SERVICE_RUNNER in runner_fields


def Deploy(
    args: argparse.Namespace,
    *,
    packager: dbt.DbtPackager | None = None,
    storage_client: gcs_client.GcsClient | None = None,
) -> dict[str, Any]:
  """Packages local action artifacts, uploads them, and deploys the pipeline.

  Args:
    args: The parsed command-line arguments.
    packager: Optional dbt packager (injected in tests).
    storage_client: Optional Cloud Storage client (injected in tests).

  Returns:
    The deployment result as a dict (see `DeployResult`).

  Raises:
    calliope_exceptions.InvalidArgumentException: If a Cloud Composer-only
      `deploy` flag is set.
    errors.PipelineLoadError: If the pipeline YAML cannot be loaded.
    errors.PackagingError: If the dbt project cannot be packaged.
    errors.UploadError: If an artifact upload fails.
    errors.NotImplementedYetError: Until the rest of the deployment flow is
      implemented.
  """
  _VerifyComposerOnlyFlagsAreUnset(args)
  loaded_pipeline = pipeline_loader.LoadPipeline(args)
  version_id = _GenerateVersionId()
  packager = packager or dbt.DbtPackager()
  storage_client = storage_client or gcs_client.GcsClient()

  uploaded_artifacts_by_action = _PackageAndUploadActions(
      loaded_pipeline, version_id, packager, storage_client
  )
  # TODO(b/567520802): pipeline_compiler.CompilePipeline ->
  # clients.orchestration_client.OrchestrationClient Create/UpdatePipeline ->
  # DeployResult.
  del uploaded_artifacts_by_action
  raise errors.NotImplementedYetError(
      "Serverless Orchestration pipeline compilation is not yet implemented."
  )


def _GetRunnerFieldsFromPipelineFiles(
    environment_name: str | None,
) -> list[Any]:
  """Returns the `runner` field of each configured pipeline YAML."""
  pipeline_file_paths = pipeline_loader.GetPipelineFilePaths(environment_name)
  return [
      pipeline_loader.LoadRawYamlMapping(pipeline_file_path).get("runner")
      for pipeline_file_path in pipeline_file_paths
  ]


def _HasStandaloneDefaultPipelineFile() -> bool:
  """Returns True if `./pipeline.yaml` exists without `./deployment.yaml`."""
  working_directory = pathlib.Path.cwd()
  return (
      not (working_directory / yaml_processor.DEPLOYMENT_FILE_NAME).is_file()
      and (
          working_directory / pipeline_loader.DEFAULT_PIPELINE_FILE_NAME
      ).is_file()
  )


def _VerifyAllPipelinesShareSameRunnerField(
    runner_fields: Sequence[Any],
) -> None:
  """Verifies no other `runner` field is mixed with `orchestration_service`."""
  if pipeline_loader.ORCHESTRATION_SERVICE_RUNNER in runner_fields and any(
      runner_field != pipeline_loader.ORCHESTRATION_SERVICE_RUNNER
      for runner_field in runner_fields
  ):
    raise errors.PipelineLoadError(
        "Cannot mix `runner: orchestration_service` with other runners in"
        " `deployment.yaml`."
    )


def _VerifyComposerOnlyFlagsAreUnset(args: argparse.Namespace) -> None:
  """Verifies no Cloud Composer-only `deploy` flag is set."""
  composer_only_flag_values = {
      "--validate": args.validate,
      "--rollback": args.rollback,
      "--version": args.version,
      "--local": args.local,
      "--paused": args.paused,
  }
  for flag_name, flag_value in composer_only_flag_values.items():
    if flag_value:
      raise calliope_exceptions.InvalidArgumentException(
          flag_name,
          "This flag is not supported for `runner: orchestration_service`"
          " pipelines.",
      )


def _GenerateVersionId() -> str:
  """Generates a UTC timestamp version ID (`vYYYYmmdd-HHMMSS`)."""
  return datetime.datetime.now(datetime.timezone.utc).strftime("v%Y%m%d-%H%M%S")


def _PackageAndUploadActions(
    loaded_pipeline: pipeline_loader.LoadedPipeline,
    version_id: str,
    packager: dbt.DbtPackager,
    storage_client: gcs_client.GcsClient,
) -> dict[str, tuple[gcs_client.UploadedArtifact, ...]]:
  """Packages all actions, then uploads their files to Cloud Storage."""
  with files.TemporaryDirectory() as staging_directory:
    packaged_artifacts = _PackageActions(
        loaded_pipeline, packager, pathlib.Path(staging_directory)
    )
    return _UploadPackagedArtifacts(
        loaded_pipeline, version_id, packaged_artifacts, storage_client
    )


def _PackageActions(
    loaded_pipeline: pipeline_loader.LoadedPipeline,
    packager: dbt.DbtPackager,
    staging_directory: pathlib.Path,
) -> list[models.PackagedArtifact]:
  """Packages each action in `loaded_pipeline` into `staging_directory`."""
  packaging_context = models.PackagingContext(
      pipeline_id=loaded_pipeline.pipeline_id,
      target=loaded_pipeline.target,
      staging_dir=staging_directory,
  )
  packaged_artifacts = []
  for action in loaded_pipeline.actions:
    log.status.Print(f"Packaging action '{action.name}'...")
    packaged_artifacts.append(packager.Package(action, packaging_context))
  return packaged_artifacts


def _UploadPackagedArtifacts(
    loaded_pipeline: pipeline_loader.LoadedPipeline,
    version_id: str,
    packaged_artifacts: Sequence[models.PackagedArtifact],
    storage_client: gcs_client.GcsClient,
) -> dict[str, tuple[gcs_client.UploadedArtifact, ...]]:
  """Uploads each action's packaged files to `<version_prefix>/<action>`."""
  artifact_prefix = gcs_client.BuildVersionedArtifactPrefix(
      loaded_pipeline.pipeline_id,
      version_id,
      loaded_pipeline.artifact_path_prefix,
  )
  uploaded_artifacts_by_action = {}
  for packaged_artifact in packaged_artifacts:
    action_prefix = f"{artifact_prefix}/{packaged_artifact.action_name}"
    log.status.Print(
        f"Uploading artifacts of action '{packaged_artifact.action_name}' to"
        f" gs://{loaded_pipeline.artifact_bucket}/{action_prefix}/..."
    )
    uploaded_artifacts_by_action[packaged_artifact.action_name] = (
        storage_client.UploadWithPrefix(
            packaged_artifact.files,
            loaded_pipeline.artifact_bucket,
            action_prefix,
        )
    )
  return uploaded_artifacts_by_action
