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
from collections.abc import Iterator, Mapping, Sequence
import contextlib
import dataclasses
import datetime
import itertools
import pathlib
from typing import Any
import uuid

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import pipeline_compiler
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import pipeline_loader
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.clients import gcs_client
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.clients import orchestration_client
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.packagers import dbt
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.packagers import models
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files

# `Pipeline` fields that `pipeline_compiler.CompilePipeline` owns; listing them
# clears any the new body omits.
_PIPELINE_UPDATE_MASK = "spec,execution_identity,output_artifact_storage"


@dataclasses.dataclass(frozen=True)
class DeployResult:
  """Result of deploying a Serverless Orchestration pipeline.

  Attributes:
    pipeline_name: `projects/*/locations/*/pipelines/*` name of the pipeline.
    version_id: Version ID of this deployment (`vYYYYmmdd-HHMMSS`).
    artifacts: `gs://` URIs of the artifacts uploaded for all actions.
    operation: Name of the create or update long-running operation, or None if
      the API response omits it.
    status: `SUCCEEDED` once the operation completed; `PENDING` with `--async`
      or when the wait was interrupted.
  """

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
    api_client: orchestration_client.OrchestrationClient | None = None,
) -> dict[str, Any]:
  """Packages local action artifacts, uploads them, and deploys the pipeline.

  Args:
    args: The parsed command-line arguments.
    packager: Optional dbt packager (injected in tests).
    storage_client: Optional Cloud Storage client (injected in tests).
    api_client: Optional Orchestration service client (injected in tests).

  Returns:
    The deployment result as a dict (see `DeployResult`).

  Raises:
    calliope_exceptions.InvalidArgumentException: If a Cloud Composer-only
      `deploy` flag is set.
    errors.PipelineLoadError: If the pipeline YAML cannot be loaded.
    errors.PackagingError: If a dbt project cannot be packaged.
    errors.UploadError: If an artifact upload fails.
    errors.OrchestrationApiError: If an Orchestration API call fails.
    errors.PipelineCompileError: If pipeline compilation fails.
  """
  _VerifyComposerOnlyFlagsAreUnset(args)
  loaded_pipeline = pipeline_loader.LoadPipeline(args)
  with _UseProjectForApiCalls(loaded_pipeline.project):
    return _DeployLoadedPipeline(
        args,
        loaded_pipeline,
        packager or dbt.DbtPackager(),
        storage_client or gcs_client.GcsClient(),
        api_client or orchestration_client.OrchestrationClient(),
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
      # `--no-paused` sets `paused` to False, so only None means it is unset.
      "--paused": args.paused is not None,
  }
  for flag_name, flag_value in composer_only_flag_values.items():
    if flag_value:
      raise calliope_exceptions.InvalidArgumentException(
          flag_name,
          "This flag is not supported for `runner: orchestration_service`"
          " pipelines.",
      )


@contextlib.contextmanager
def _UseProjectForApiCalls(project: str) -> Iterator[None]:
  """Sets `core/project` to `project` inside the block, over `--project`."""
  # An invocation value outranks `--project`, whereas `Property.Set()` only
  # sets an environment variable. `billing/quota_project` is left as is: its
  # `CURRENT_PROJECT` default already makes `core/project` the quota project
  # for user credentials, and an explicit `--billing-project` still applies.
  properties.VALUES.PushInvocationValues()
  try:
    properties.VALUES.SetInvocationValue(
        properties.VALUES.core.project, project, None
    )
    yield
  finally:
    properties.VALUES.PopInvocationValues()


def _DeployLoadedPipeline(
    args: argparse.Namespace,
    loaded_pipeline: pipeline_loader.LoadedPipeline,
    packager: dbt.DbtPackager,
    storage_client: gcs_client.GcsClient,
    api_client: orchestration_client.OrchestrationClient,
) -> dict[str, Any]:
  """Packages and uploads `loaded_pipeline`, then creates or updates it."""
  pipeline_name = pipeline_compiler.BuildPipelineResourceName(loaded_pipeline)
  # Looked up first so auth and IAM errors surface before anything is uploaded.
  existing_pipeline = api_client.GetPipeline(pipeline_name)
  version_id = _GenerateVersionId()
  uploaded_artifacts_by_action = _PackageAndUploadActions(
      loaded_pipeline, version_id, packager, storage_client
  )
  compiled_pipeline = pipeline_compiler.CompilePipeline(
      loaded_pipeline, uploaded_artifacts_by_action, version_id
  )
  operation = _CreateOrUpdatePipeline(
      api_client, compiled_pipeline, update=existing_pipeline is not None
  )
  status = _WaitForDeployment(
      api_client, compiled_pipeline.pipeline_id, operation, args.async_
  )
  return _BuildDeployResult(
      compiled_pipeline, uploaded_artifacts_by_action, operation, status
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


def _CreateOrUpdatePipeline(
    api_client: orchestration_client.OrchestrationClient,
    compiled_pipeline: pipeline_compiler.CompiledPipeline,
    update: bool,
) -> Mapping[str, Any]:
  """Creates or updates `compiled_pipeline` and returns the LRO."""
  log.status.Print(f"Deploying pipeline '{compiled_pipeline.pipeline_id}'...")
  # Lets the API ignore a duplicate of this request if the first one timed out.
  request_id = str(uuid.uuid4())
  if update:
    return api_client.UpdatePipeline(
        name=compiled_pipeline.name,
        body=compiled_pipeline.body,
        update_mask=_PIPELINE_UPDATE_MASK,
        request_id=request_id,
    )
  return api_client.CreatePipeline(
      parent=compiled_pipeline.parent,
      pipeline_id=compiled_pipeline.pipeline_id,
      body=compiled_pipeline.body,
      request_id=request_id,
  )


def _WaitForDeployment(
    api_client: orchestration_client.OrchestrationClient,
    pipeline_id: str,
    operation: Mapping[str, Any],
    async_: bool,
) -> str:
  """Waits for `operation` unless `async_`; returns `DeployResult.status`."""
  operation_name = operation.get("name")
  if async_:
    log.status.Print(
        f"Deployment of pipeline '{pipeline_id}' started (operation"
        f" {operation_name}). Exiting due to --async flag."
    )
    return "PENDING"
  try:
    api_client.WaitOperation(operation)
  except KeyboardInterrupt:
    log.status.Print(
        f"Interrupted; the deployment of pipeline '{pipeline_id}' continues in"
        f" the background (operation {operation_name})."
    )
    return "PENDING"
  return "SUCCEEDED"


def _BuildDeployResult(
    compiled_pipeline: pipeline_compiler.CompiledPipeline,
    uploaded_artifacts_by_action: Mapping[
        str, Sequence[gcs_client.UploadedArtifact]
    ],
    operation: Mapping[str, Any],
    status: str,
) -> dict[str, Any]:
  """Builds the `DeployResult` dict returned by the `deploy` command."""
  uploaded_artifacts = itertools.chain.from_iterable(
      uploaded_artifacts_by_action.values()
  )
  return dataclasses.asdict(
      DeployResult(
          pipeline_name=compiled_pipeline.name,
          version_id=compiled_pipeline.version_id,
          artifacts=tuple(artifact.gcs_uri for artifact in uploaded_artifacts),
          operation=operation.get("name"),
          status=status,
      )
  )
