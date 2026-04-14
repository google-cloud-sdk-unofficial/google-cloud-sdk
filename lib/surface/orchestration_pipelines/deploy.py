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
"""Deploy command for Orchestration Pipelines."""

import argparse
import datetime
import getpass
import io
import os
import pathlib
import re
import subprocess
import time
import types
from typing import Any

from apitools.base.py import exceptions as api_exceptions
from apitools.base.py import transfer
from googlecloudsdk.api_lib.composer import dags_util as composer_dags_util
from googlecloudsdk.api_lib.composer import environments_util
from googlecloudsdk.api_lib.composer import util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines import gcp_deployer
from googlecloudsdk.command_lib.orchestration_pipelines import git_context
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import registry
from googlecloudsdk.command_lib.orchestration_pipelines.processors import action_processor
from googlecloudsdk.command_lib.orchestration_pipelines.tools import composer_utils
from googlecloudsdk.command_lib.orchestration_pipelines.tools import gcs_utils
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


DEPLOYMENT_FILE = "deployment.yaml"
MANIFEST_FILE_NAME = "manifest.yml"
ENV_PACK_FILE = "environment.tar.gz"

# Auto-generated DAG boilerplate
DAG_TEMPLATE = """import os

from orchestration_pipelines_lib.api import generate_dags

# Generate airflow DAG from pipeline definition
pipeline_name = os.path.splitext(os.path.basename(__file__))[0]
generate_dags("/home/airflow/gcs/data", "{bundle_id}", pipeline_name)
"""


class DeployError(exceptions.Error):
  """Exception for errors during the deploy process."""
  pass


def _GetRepoName(subprocess_mod: Any) -> str:
  """Gets the repository name from git remote origin or falls back to CWD."""
  try:
    url = subprocess_mod.check_output(
        ["git", "remote", "get-url", "origin"],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()
    base = url.split("/")[-1]
    if base.endswith(".git"):
      return base[:-4]
    return base
  except (subprocess_mod.CalledProcessError, FileNotFoundError):
    return pathlib.Path.cwd().name


def _GetComposerBucket(env_name: str, location: str) -> str:
  """Retrieves the GCS bucket for the Composer environment."""
  try:
    project = properties.VALUES.core.project.Get(required=True)
    env_ref = resources.REGISTRY.Parse(
        env_name,
        params={
            "projectsId": project,
            "locationsId": location,
        },
        collection="composer.projects.locations.environments",
    )
    env_obj = environments_util.Get(env_ref)
    if not env_obj.config or not env_obj.config.dagGcsPrefix:
      raise DeployError(
          f"Failed to retrieve Composer bucket from environment '{env_name}'."
          " Ensure the environment exists and is fully initialized."
      )
    bucket = env_obj.config.dagGcsPrefix.replace("gs://", "").split("/")[0]
    return bucket
  except Exception as e:
    current_project = properties.VALUES.core.project.Get() or "[NOT SET]"
    raise DeployError(
        f"Failed to find Composer environment '{env_name}' in region"
        f" '{location}' for project '{current_project}'. Please verify you are"
        " authenticated to the correct Google Cloud project"
        " (`gcloud config set project <PROJECT_ID>`) and the environment"
        " exists.\nDetails: {e}"
        f"and the environment exists.\nDetails: {e}"
    ) from e


def _UploadDirToGcs(local_dir: pathlib.Path, dest_uri: str) -> None:
  """Uploads a local directory recursively to GCS.

  Args:
    local_dir: pathlib.Path, the local directory to upload.
    dest_uri: str, the destination GCS URI.
  """

  storage_client = storage_api.StorageClient()
  dest_ref = storage_util.ObjectReference.FromUrl(
      dest_uri, allow_empty_object=True
  )

  for root, _, dirs in os.walk(local_dir):
    for f in dirs:
      local_path = os.path.join(root, f)
      rel_path = os.path.relpath(local_path, local_dir)
      # Ensure GCS paths use forward slashes
      gcs_path = rel_path.replace(os.path.sep, "/")

      obj_ref = storage_util.ObjectReference.FromName(
          dest_ref.bucket,
          f"{dest_ref.object.rstrip('/')}/{gcs_path}".lstrip("/"),
      )
      storage_client.CopyFileToGCS(local_path, obj_ref)


def _UploadFile(
    content: str | bytes,
    dest: str,
    file_name: str,
    if_generation_match: int | None = None,
) -> None:
  """Uploads files to GCS, optionally with optimistic locking."""

  storage_client = storage_api.StorageClient()
  dest_ref = storage_util.ObjectReference.FromUrl(dest)

  content_bytes = (
      content.encode("utf-8") if isinstance(content, str) else content
  )
  stream = io.BytesIO(content_bytes)

  upload = transfer.Upload.FromStream(stream, mime_type="text/plain")
  insert_req = storage_client.messages.StorageObjectsInsertRequest(
      bucket=dest_ref.bucket,
      name=dest_ref.object,
      object=storage_client.messages.Object(size=len(content_bytes)),
  )

  if if_generation_match is not None:
    insert_req.ifGenerationMatch = int(if_generation_match)

  try:
    storage_client.client.objects.Insert(insert_req, upload=upload)
  except api_exceptions.HttpConflictError as e:
    # 412 Precondition Failed can act like HttpConflictError for optimistic
    # locking.
    raise calliope_exceptions.HttpException(
        "Precondition Failed (Optimistic Lock Mismatch)"
    ) from e
  except api_exceptions.HttpError as e:
    if e.status_code == 412:
      raise calliope_exceptions.HttpException(
          "Precondition Failed (Optimistic Lock Mismatch)"
      )
    log.error("Failed to upload %s to %s: %s", file_name, dest, e)
    raise DeployError("File upload to GCS failed.") from e


def _FetchManifest(
    bucket: str, manifest_dir_path: str
) -> tuple[dict[str, Any] | None, int]:
  """Fetches manifest content and its GCS generation ID from a specific path."""

  storage_client = storage_api.StorageClient()
  manifest_path = f"gs://{bucket}/{manifest_dir_path}/{MANIFEST_FILE_NAME}"
  manifest_ref = storage_util.ObjectReference.FromUrl(manifest_path)

  try:
    obj = storage_client.GetObject(manifest_ref)
    generation = obj.generation
  except api_exceptions.HttpNotFoundError:
    return None, 0

  try:
    with storage_client.ReadObject(manifest_ref) as content_stream:
      content = content_stream.read()
    return yaml.load(content), generation
  except (exceptions.Error, api_exceptions.HttpError):
    return None, 0


def _NormalizeArtifactPath(path: str | None) -> str | None:
  """Normalizes artifact path to be either absolute or gs path."""
  if path and isinstance(path, str):
    if not path.startswith("gs://") and not path.startswith("/"):
      path = "/" + (path[2:] if path.startswith("./") else path)
  return path


def _GetRelativePath(path: str) -> str:
  """Returns path relative to bundle dir, removing leading '/' and './'."""
  path = path.lstrip("/")
  if path.startswith("./"):
    path = path[2:]
  return path


def _DeployGcpResources(parsed_deployment: dict[str, Any]) -> int:
  """Deploys GCP resources based on a deployment dict.

  Args:
    parsed_deployment: The already parsed deployment dict.

  Returns:
    The number of resources deployed.
  """
  resources_deployed_count = 0
  deployment_resources = parsed_deployment.get("resources", [])

  environment_obj = types.SimpleNamespace(**parsed_deployment)

  for resource in deployment_resources:
    if resource.type == "resourceProfile":
      log.status.Print(f"Skipping resource profile '{resource.name}'.")
      continue
    handler = registry.GetHandler(resource, environment_obj)
    gcp_deployer.validate_gcp_resource_l1(handler)
    gcp_deployer.deploy_gcp_resource(handler)
    resources_deployed_count += 1
  return resources_deployed_count


def _ArtifactsExist(artifact_uri: str) -> bool:
  """Checks if any artifacts already exist in GCS for the given URI prefix.

  This is used as an optimization for rollbacks to skip re-uploading if
  artifacts for the specific version are already present.

  Args:
    artifact_uri: The base GCS URI for the artifacts.

  Returns:
    True if at least one object exists under the artifact_uri prefix, False
    otherwise.
  """

  storage_client = storage_api.StorageClient()
  try:
    obj_ref = storage_util.ObjectReference.FromUrl(
        artifact_uri, allow_empty_object=True
    )
    bucket_ref = storage_util.BucketReference.FromArgument(
        f"gs://{obj_ref.bucket}"
    )
    prefix = obj_ref.object
  except exceptions.Error:
    return False

  try:
    return any(
        True for _ in storage_client.ListBucket(bucket_ref, prefix=prefix)
    )
  except api_exceptions.HttpError:
    return False


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class Deploy(calliope_base.Command):
  """Deploy a pipeline."""

  def __init__(self, *args, subprocess_mod=subprocess, **kwargs):
    super().__init__(*args, **kwargs)
    self._subprocess = subprocess_mod

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--validate",
        action="store_true",
        help="If set, performs full validation for resources and pipelines.",
    )
    parser.add_argument(
        "--environment",
        required=True,
        help="The target environment for the deployment.",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="If set, performs a rollback to a specified version.",
    )
    parser.add_argument(
        "--version",
        help=(
            "The git SHA version to rollback to. Required if `--rollback` is"
            " set."
        ),
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help=(
            "If set, performs a local deployment without requiring Git. "
            "Rollback logic will be disabled."
        ),
    )
    parser.add_argument(
        "--pipeline",
        help=(
            "Deploy a specific pipeline by ID, name, or source file. "
            "Particularly useful for speeding up `--local` deployments."
        ),
    )
    parser.add_argument(
        "--paused",
        action=arg_parsers.StoreTrueFalseAction,
        help=(
            "Adds the deployed pipelines to the paused_pipelines list. Defaults"
            " to true for local deployments, meaning the pipeline will be"
            " automatically paused. Use `--no-paused` to explicitly unpause."
            " Currently only supported when using the `--local` flag."
        ),
    )
    parser.add_argument(
        "--async",
        dest="async_",
        action="store_true",
        help=(
            "If set, deploys asynchronously without waiting for the information"
            " about all the pipelines in the bundle to become available."
        ),
    )
    parser.add_argument(
        "--substitutions",
        metavar="KEY=VALUE",
        type=arg_parsers.ArgDict(),
        help="Variables to substitute in the pipeline configuration.",
    )
    parser.add_argument(
        "--substitutions-file",
        help=(
            "Path to a YAML file containing variable substitutions for the "
            "pipeline configuration."
        ),
    )

  def Run(self, args: argparse.Namespace) -> None:
    work_dir = pathlib.Path.cwd()
    status = {
        "resource_deployment": "SKIPPED",
        "pipeline_deployment": "SKIPPED",
    }

    # 1. Start with built-in/ephemeral
    external_vars = {}

    # 2. Command-line substitutions overrides built-ins
    substitutions_file_vars = {}
    if getattr(args, "substitutions_file", None):
      try:
        substitutions_file_vars = yaml.load_path(args.substitutions_file)
        if not isinstance(substitutions_file_vars, dict):
          raise calliope_exceptions.BadFileException(
              f"Substitutions file {args.substitutions_file} "
              "must contain a dictionary."
          )
      except yaml.Error as e:
        raise calliope_exceptions.BadFileException(
            f"Error parsing substitutions file {args.substitutions_file}: {e}"
        ) from e

    env_vars = yaml_processor.collect_environment_variables()

    # 3. Apply precedence: built-ins <- env vars <- file <- flags
    external_vars.update(env_vars)
    external_vars.update(substitutions_file_vars)
    if getattr(args, "substitutions", None):
      external_vars.update(args.substitutions)

    explicit_version = None

    is_paused = getattr(args, "paused", None)

    if is_paused is not None and not getattr(args, "local", False):
      raise DeployError(
          "Invalid Arguments: --paused is currently only allowed "
          "when using --local mode."
      )
    # For --local, default to True if omitted.
    if getattr(args, "local", False) and is_paused is None:
      is_paused = True

    if args.version:
      if args.rollback:
        explicit_version = args.version
        external_vars["COMMIT_SHA"] = args.version
        if "COMMIT_SHA" in external_vars:
          log.warning(
              "Both --version and COMMIT_SHA provided. COMMIT_SHA will be"
              " ignored in favor of --version for rollback."
          )
      else:
        log.warning(
            "--version is only applicable with --rollback. Ignoring provided"
            " version %s.",
            args.version,
        )

    git_context_obj = git_context.GitContext(
        self._subprocess,
        explicit_version,
        bundle_path=work_dir,
        is_local=getattr(args, "local", False),
    )

    if "COMMIT_SHA" not in external_vars:
      external_vars["COMMIT_SHA"] = git_context_obj.GetSafeCommitSha()

    if getattr(args, "pipeline", None) and not args.local:
      raise DeployError(
          "Invalid Arguments: --pipeline can only be used in conjunction "
          "with the --local flag for local deployments."
      )
    if args.local:
      if args.rollback:
        raise DeployError(
            "Invalid Arguments: --rollback is not available when "
            "using --local mode. Local deployments use ephemeral version IDs."
        )

    if args.rollback:
      if not args.version:
        raise calliope_exceptions.RequiredArgumentException(
            "--version", "Version (SHA) is required when --rollback is set."
        )
      log.status.Print(
          f"Prepare Rollback: Checking out version {args.version}..."
      )
      try:
        self._subprocess.check_call(["git", "checkout", args.version])
      except subprocess.CalledProcessError as e:
        raise DeployError(
            f"Rollback failed: Could not rollback to version {args.version}. "
            f"Git error: {e}"
        ) from e

    bundle_dir = work_dir
    deployment_path = bundle_dir / DEPLOYMENT_FILE

    try:
      parsed_deployment, combined_variables = yaml_processor.parse_deployment(
          deployment_path, args.environment, external_vars
      )
    except (yaml.FileLoadError, yaml.YAMLParseError) as e:
      raise calliope_exceptions.BadFileException(
          "Deployment file not found or failed to parse: "
          f"{deployment_path.name}"
      ) from e
    except yaml_processor.BadFileError as e:
      raise DeployError(
          f"Failed to process deployment for environment '{args.environment}' "
          f"from file '{deployment_path.name}':\n{e}"
      ) from e

    env_project = parsed_deployment.get("project")
    orig_project = properties.VALUES.core.project.Get()
    if env_project:
      properties.VALUES.core.project.Set(env_project)

    try:
      try:
        log.status.Print(
            f"Deployment file {deployment_path.name} found, deploying "
            "resources..."
        )
        resources_deployed_count = _DeployGcpResources(parsed_deployment)
        if resources_deployed_count > 0:
          status["resource_deployment"] = "SUCCESS"
        else:
          status["resource_deployment"] = "SKIPPED"
      except Exception as e:
        raise DeployError(
            f"Failed to deploy resources for environment '{args.environment}' "
            f"from file '{deployment_path.name}':\n{e}"
        ) from e

      pipelines = [
          pipeline.source
          for pipeline in parsed_deployment.get("pipelines", [])
          if pipeline.source
      ]
      single_pipeline_source = None
      if getattr(args, "pipeline", None):
        single_pipeline_source = args.pipeline
        filtered_pipelines = []
        for p in pipelines:
          if args.pipeline == p:
            filtered_pipelines.append(p)
        if not filtered_pipelines:
          raise DeployError(
              f"Pipeline '{args.pipeline}' not found in {DEPLOYMENT_FILE}."
          )
        pipelines = filtered_pipelines
      if args.local:
        try:
          raw_user = getpass.getuser()
        except (OSError, ImportError, KeyError):
          raw_user = "localdev"
        clean_user = re.sub(r"[^a-z0-9]", "", raw_user.lower())
        clean_dir = re.sub(r"[^a-z0-9]", "", bundle_dir.name.lower())
        bundle_name = f"bundle-local-{clean_user}-{clean_dir}"
      else:
        bundle_name = _GetRepoName(self._subprocess)

      version_id = None
      if pipelines:
      # TODO(b/497670530): Re-enable L1 validation next week after backend is
      # ready.
      # yaml_processor.validate_pipeline_l1(
      #     bundle_dir, pipelines, combined_variables
      # )
        composer_bucket = _GetComposerBucket(
            parsed_deployment["composer_env"],
            parsed_deployment["region"],
        )
        for pipeline in pipelines:
          yaml_path = bundle_dir / pipeline
          version_id = self._DeployPipeline(
              bundle_dir,
              yaml_path,
              git_context_obj,
              rollback=args.rollback,
              bundle_name=bundle_name,
              is_paused=is_paused,
              composer_bucket=composer_bucket,
              is_local=getattr(args, "local", False),
              parsed_deployment=parsed_deployment,
              combined_variables=combined_variables,
          )
        status["version"] = version_id

        if getattr(args, "async_", False):
          status["pipeline_deployment"] = "SUCCESS"
          log.status.Print(
              f"\nAsynchronous mode complete.\nBundle ID: {bundle_name}\n"
              f"Version ID: {status['version']}\n"
          )
        else:
          try:
            single_pipeline_id = None
            if single_pipeline_source:
              single_pipeline_id = pathlib.Path(single_pipeline_source).stem
            wait_result = self._WaitForPipelines(
                bundle_name=bundle_name,
                expected_pipelines_count=len(pipelines),
                composer_env_name=parsed_deployment["composer_env"],
                location=parsed_deployment["region"],
                project=parsed_deployment["project"],
                version_id=status["version"],
                single_pipeline_name=single_pipeline_id,
                is_paused=is_paused,
            )
            deployed_pipelines = wait_result.get("pipelines", [])
            all_healthy = True
            log.status.Print(
                f"\nSync mode complete.\nBundle ID: {bundle_name}\nVersion"
                f" ID: {status['version']}\n"
            )
            if not deployed_pipelines:
              log.status.Print("\n--- Pipeline Deployment Status ---")
              log.status.Print("No pipelines deployed successfully.")
              all_healthy = False
            else:
              log.status.Print("\n--- Pipeline Deployment Status ---")
              for p in deployed_pipelines:
                p_id = p.get("pipeline_id", "Unknown")
                p_status = p.get("status", "unknown").upper()
                if p_status == "HEALTHY":
                  log.status.Print(
                      f"Pipeline '{p_id}': [OK] (Status: {p_status})"
                  )
                else:
                  log.error(f"Pipeline '{p_id}': [FAILED] (Status: {p_status})")
                  all_healthy = False
            log.status.Print("\n--- Pipeline Deployment full details ---")
            log.status.Print(f"Deployed pipelines: {deployed_pipelines}")

            if not all_healthy:
              status["pipeline_deployment"] = "FAILED"
            else:
              status["pipeline_deployment"] = "SUCCESS"

          except DeployError as e:
            status["pipeline_deployment"] = "FAILED"
            log.error(
                "Failed to wait for pipelines to be parsed in Composer. "
                "Error: %s",
                e,
            )

      if status["pipeline_deployment"] == "FAILED":
        raise DeployError(
            "Deployment failed: One or more pipelines are in an UNHEALTHY "
            "state. Check Airflow logs for parsing errors."
        )
      if args.validate:
        environment_model = yaml_processor.load_environment(
            deployment_path, args.environment, external_vars
        )
        yaml_processor.validate_pipeline_l2(
            bundle_dir, pipelines, combined_variables, environment_model
        )

      success_states = ["SUCCESS", "SKIPPED"]

      if (
          status["resource_deployment"] not in success_states
          and status["pipeline_deployment"] not in success_states
      ):
        raise DeployError(
            f"Failed to deploy. Searched recursively in {work_dir}, "
            "but found no valid bundles containing both a pipeline YAML "
            f"(with pipelineId) and a {DEPLOYMENT_FILE} for environment "
            f"'{args.environment}'."
        )

      if (
          status["pipeline_deployment"] == "SUCCESS"
          and status["resource_deployment"] == "SUCCESS"
      ):
        log.status.Print(
            "Resource and pipeline deployment successful for version"
            f" {status['version']} in bundle '{bundle_name}'"
        )
      elif status["pipeline_deployment"] == "SUCCESS":
        log.status.Print(
            f"Pipeline deployment successful for version {status['version']} in"
            f" bundle '{bundle_name}'"
        )
      elif status["resource_deployment"] == "SUCCESS":
        log.status.Print("Resource deployment successful.")
    finally:
      if env_project:
        properties.VALUES.core.project.Set(orig_project)

  def _WaitForPipelines(
      self,
      bundle_name,
      expected_pipelines_count,
      composer_env_name,
      location,
      project,
      version_id: str,
      single_pipeline_name=None,
      is_paused=None,
  ):
    """Waits for pipelines to be parsed in Composer."""
    timeout = 300
    sleep_time = 10
    start_time = time.time()
    dags = []

    api_version = util.GetApiVersion(self.ReleaseTrack())
    environment_resource_name = f"projects/{project}/locations/{location}/environments/{composer_env_name}"
    environment_ref = resources.REGISTRY.ParseRelativeName(
        environment_resource_name,
        collection="composer.projects.locations.environments",
        api_version=api_version,
    )
    log.status.Print(
        f"Waiting up to 5 minutes for {expected_pipelines_count} pipeline(s) in"
        f" bundle '{bundle_name}' to become available in Composer..."
    )

    while time.time() - start_time < timeout:
      try:
        list_filter = composer_utils.build_dags_filter_tags(
            bundle=bundle_name,
            pipeline=single_pipeline_name,
            is_current=True,
            version=version_id,
        )

        response = composer_dags_util.ListDags(
            environment_ref,
            list_filter=list_filter,
        )
        dags = getattr(response, "dags", []) or []

        dags_ready = (
            (len(dags) == 1)
            if single_pipeline_name
            else (len(dags) == expected_pipelines_count)
        )

        if dags_ready:
          if not is_paused:
            for d in dags:
              dag_ref = resources.REGISTRY.ParseRelativeName(
                  d.name,
                  collection="composer.projects.locations.environments.dags",
                  api_version=api_version,
              )
              pipeline_id = d.name.split("/")[-1]
              log.status.Print(f"Activating pipeline {pipeline_id}...")
              composer_dags_util.ActivateDag(dag_ref)

          if single_pipeline_name:
            dag_ref = resources.REGISTRY.ParseRelativeName(
                dags[0].name,
                collection="composer.projects.locations.environments.dags",
                api_version=api_version,
            )
            list_tasks_response = composer_dags_util.ListTasks(dag_ref)
            tasks = getattr(list_tasks_response, "tasks", [])

            if tasks:
              log.status.Print(
                  "Sync mode complete: Single pipeline DAG and tasks"
                  " successfully registered."
              )
              pipelines_result = composer_utils.convert_dags_to_pipelines(dags)
              pipelines_result[0]["actions"] = (
                  composer_utils.convert_tasks_to_actions(tasks)
              )
              return {"pipelines": pipelines_result}
          else:
            log.status.Print(
                "Sync mode complete: Multiple pipeline DAGs successfully"
                " registered."
            )
            return {"pipelines": composer_utils.convert_dags_to_pipelines(dags)}
      except DeployError as e:
        log.error(
            "Failed to retrieve pipeline status from Composer, retrying..."
            " Error: %s",
            e,
        )

      elapsed_time = int(time.time() - start_time)
      log.status.Print(f"Waiting... ({elapsed_time}s elapsed)")
      time.sleep(sleep_time)

    log.warning(
        "Timeout waiting 5 minutes for pipelines to register. "
        f"Found {len(dags)} / {expected_pipelines_count} expected pipelines."
    )
    return {}

  def _ResolveAndQueuePath(
      self,
      raw_path: Any,
      rewrite_to_gcs: bool,
      artifact_base_uri: str,
      action_filenames_to_upload: set[str],
  ) -> Any:
    """Queues a path for upload and returns the final path for the YAML."""
    if not raw_path or not isinstance(raw_path, str):
      return raw_path

    if raw_path.startswith("gs://"):
      if rewrite_to_gcs:
        action_filenames_to_upload.add(raw_path)
      return raw_path

    clean_path = _GetRelativePath(raw_path)
    parent_dir = str(pathlib.Path(clean_path).parent)

    queue_target = (
        parent_dir if parent_dir and parent_dir != "." else clean_path
    )
    action_filenames_to_upload.add(queue_target)

    return f"{artifact_base_uri}{clean_path}" if rewrite_to_gcs else clean_path

  def _ProcessAndUploadArtifacts(
      self,
      resolved_pipeline: dict[str, Any],
      bundle_dir: pathlib.Path,
      composer_bucket: str,
      bundle_data_prefix: str,
      version_id,
      artifact_base_uri: str,
  ) -> None:
    """Processes actions and uploads artifacts to GCS."""
    uploaded_framework_projects = set[str]()
    action_filenames_to_upload = set[str]()
    env_pack_files_to_upload = set[str]()

    defaults = resolved_pipeline.get("defaults", {})
    allowed_processor_engines = {"dataprocServerless", "dataprocOnGce"}

    for action_item in resolved_pipeline.get("actions", []):
      action = action_item
      action_type = None
      if isinstance(action_item, dict):
        if "pipeline" in action_item and isinstance(
            action_item["pipeline"], dict
        ):
          action = action_item["pipeline"]
          action_type = "pipeline"
        elif "pyspark" in action_item and isinstance(
            action_item["pyspark"], dict
        ):
          action = action_item["pyspark"]
          action_type = "pyspark"
        elif "notebook" in action_item and isinstance(
            action_item["notebook"], dict
        ):
          action = action_item["notebook"]
          action_type = "notebook"
        elif "sql" in action_item and isinstance(action_item["sql"], dict):
          action = action_item["sql"]
          action_type = "sql"
        elif "python" in action_item and isinstance(
            action_item["python"], dict
        ):
          action = action_item["python"]
          action_type = "python"
        elif len(action_item) == 1:
          first_key = next(iter(action_item.keys()))
          if isinstance(action_item[first_key], dict):
            action = action_item[first_key]
            action_type = first_key

      engine_dict = action.get("engine", {})

      if "mainFilePath" in action:
        needs_gcs_rewrite = action_type in ["pyspark", "notebook"]
        action["mainFilePath"] = self._ResolveAndQueuePath(
            raw_path=action["mainFilePath"],
            rewrite_to_gcs=needs_gcs_rewrite,
            artifact_base_uri=artifact_base_uri,
            action_filenames_to_upload=action_filenames_to_upload,
        )
      if (
          action_type == "sql"
          and isinstance(action.get("query"), dict)
          and "path" in action["query"]
      ):
        is_serverless = "dataprocServerless" in engine_dict
        action["query"]["path"] = self._ResolveAndQueuePath(
            raw_path=action["query"]["path"],
            rewrite_to_gcs=is_serverless,
            artifact_base_uri=artifact_base_uri,
            action_filenames_to_upload=action_filenames_to_upload,
        )

      py_files = action.get("pyFiles")
      if py_files and isinstance(py_files, list):
        normalized = [_NormalizeArtifactPath(f) for f in py_files]
        action_filenames_to_upload.update(normalized)
        action["pyFiles"] = normalized

      clean_path = action_item.pop("_local_framework_upload_path", None)
      if clean_path and clean_path not in uploaded_framework_projects:
        uploaded_framework_projects.add(clean_path)
        local_project_path = bundle_dir / clean_path

        if local_project_path.exists():
          log.status.Print(
              f"Uploading '{clean_path}' to pipeline data folder..."
          )
          data_dest_uri = f"gs://{composer_bucket}/{bundle_data_prefix}/versions/{version_id}/{clean_path}"
          if local_project_path.is_dir():
            _UploadDirToGcs(local_project_path, data_dest_uri)
          else:
            dest_ref = storage_util.ObjectReference.FromUrl(data_dest_uri)
            storage_client = storage_api.StorageClient()
            storage_client.CopyFileToGCS(str(local_project_path), dest_ref)
        else:
          log.warning(f"Path not found locally: {clean_path}")

      reqs_path_str = None
      if action_type in ["pyspark", "notebook"]:
        env = action.get("environment")
        if isinstance(env, dict):
          reqs = env.get("requirements")
          if isinstance(reqs, dict):
            reqs_path_str = reqs.get("path")

      resolved_reqs_path = None

      if reqs_path_str:
        reqs_path_str = _GetRelativePath(reqs_path_str)
        resolved_reqs_path = bundle_dir / reqs_path_str

        if not resolved_reqs_path.exists():
          raise calliope_exceptions.BadFileException(
              f"Requirements file not found: {resolved_reqs_path}"
          )

      provided_engines = []
      if engine_dict:
        if isinstance(engine_dict, dict):
          provided_engines = list(engine_dict.keys())
          is_allowed = all(
              engine in allowed_processor_engines for engine in provided_engines
          )
        else:
          raise DeployError(
              "The 'engine' block is formatted incorrectly. Expected a"
              f" dictionary, but got: {engine_dict}"
          )
      else:
        is_allowed = False

      if is_allowed:
        processor = action_processor.get_action_processor(
            action,
            bundle_dir,
            artifact_base_uri,
            self._subprocess,
            defaults,
            requirements_path=resolved_reqs_path,
        )
        if processor:
          processor.process_action()
          env_pack_file = processor.env_pack_file
          if env_pack_file:
            env_pack_files_to_upload.add(env_pack_file)
      else:
        log.warning(
            f"Skipping requirements processing. Engine(s) {provided_engines} "
            f"are not supported. Allowed engines: {allowed_processor_engines}."
        )

    self._UploadArtifacts(
        work_dir=bundle_dir,
        artifact_uri=artifact_base_uri,
        action_filenames=action_filenames_to_upload,
        env_pack_files=env_pack_files_to_upload,
    )

  def _UpdateManifest(
      self,
      composer_bucket,
      bundle_data_prefix,
      version_id,
      git_context_obj,
      pipeline_path,
      bundle_name,
      is_paused=False,
      is_local=False,
  ):
    """Updates the manifest file in GCS with retry logic."""
    manifest_dest = (
        f"gs://{composer_bucket}/{bundle_data_prefix}/{MANIFEST_FILE_NAME}"
    )
    max_retries = 5
    attempts = 0
    local_metadata = {
        "origination": "LOCAL_DEPLOY",
    }

    metadata = (
        local_metadata
        if is_local
        else git_context_obj.GetDeploymentMetadata(version_id)
    )
    while attempts < max_retries:
      manifest_data, read_generation_id = _FetchManifest(
          composer_bucket, bundle_data_prefix
      )
      if manifest_data is None:
        manifest_data = {
            "bundle": bundle_name,
            "pausedPipelines": [],
            "versionsHistory": [],
        }
      current_time = datetime.datetime.now(datetime.timezone.utc).isoformat(
          timespec="milliseconds"
      ).replace("+00:00", "Z")
      pipeline_name = pipeline_path.stem

      paused_pipelines = manifest_data.get("pausedPipelines", [])
      if not isinstance(paused_pipelines, list):
        paused_pipelines = []

      if is_paused is not None:
        if is_paused and pipeline_name not in paused_pipelines:
          paused_pipelines.append(pipeline_name)
        elif not is_paused and pipeline_name in paused_pipelines:
          paused_pipelines.remove(pipeline_name)

      new_manifest_payload = manifest_data.copy() | {
          "bundle": bundle_name,
          "defaultVersion": str(version_id),
          "updatedAt": current_time,
          "pausedPipelines": paused_pipelines,
      }

      history = new_manifest_payload.get("versionsHistory", [])

      existing_entry = next(
          (
              item
              for item in history
              if item.get("versionId") == str(version_id)
          ),
          None,
      )

      if existing_entry:
        if pipeline_name not in existing_entry.setdefault("pipelines", []):
          existing_entry["pipelines"].append(pipeline_name)
        existing_entry["timestamp"] = current_time
        if metadata:
          existing_entry["metadata"] = metadata
      else:
        new_entry = {
            "timestamp": current_time,
            "versionId": str(version_id),
            "pipelines": [pipeline_name],
        }
        if metadata:
          new_entry["metadata"] = metadata
        history.insert(0, new_entry)

      new_manifest_payload["versionsHistory"] = history

      try:
        log.status.Print(
            "Attempting to update manifest (Generation match:"
            f" {read_generation_id})..."
        )
        _UploadFile(
            yaml.dump(new_manifest_payload),
            manifest_dest,
            MANIFEST_FILE_NAME,
            if_generation_match=read_generation_id,
        )
        break

      except calliope_exceptions.HttpException:
        attempts += 1
        log.warning(
            "Race condition detected (Conflict on generation %s). Retrying"
            " (%s/%s)...",
            read_generation_id,
            attempts,
            max_retries,
        )

    if attempts >= max_retries:
      raise DeployError(
          f"Failed to update manifest for {pipeline_path.stem} after"
          f" {max_retries} retries."
      )

  def _DeployPipeline(
      self,
      bundle_dir,
      pipeline_path,
      git_context_obj,
      rollback=False,
      bundle_name=None,
      is_paused=False,
      composer_bucket=None,
      is_local=False,
      combined_variables=None,
      parsed_deployment=None,
  ):
    """Deploys the pipeline using the dynamic context and concurrency control.

    Args:
      bundle_dir: The directory containing the pipeline bundle.
      pipeline_path: The path to the pipeline YAML file.
      git_context_obj: The GitContext object.
      rollback: If True, this is a rollback operation.
      bundle_name: The name of the bundle.
      is_paused: If True, the pipeline will be added to the paused_pipelines
        list in the manifest.
      composer_bucket: The GCS bucket of the Composer environment.
      is_local: If True, the deployment is a local deployment.
      combined_variables: Dictionary of combined variables for substitution.
      parsed_deployment: dict[str, Any], the parsed deployment configuration.

    Returns:
      The version ID (git commit hash) of the deployed pipeline.

    Raises:
      calliope_exceptions.BadFileException: If the pipeline file is not found
        or cannot be read.
      DeployError: If the manifest update fails after multiple retries.
    """
    git_context_obj.EnforceClean()
    version_id = git_context_obj.CalculateVersionId()

    bundle_data_prefix = (
        f"{gcs_utils.ORCHESTRATION_PIPELINES_DATA_DIRECTORY}/{bundle_name}"
    )
    artifact_base_uri = (
        f"gs://{parsed_deployment['artifact_storage']['bucket']}/"
        f"{parsed_deployment['artifact_storage']['path_prefix']}/"
        f"{bundle_name}/versions/{version_id}/"
    )
    dag_path = pipeline_path.with_suffix(".py")
    bundle_dag_prefix = (
        f"{gcs_utils.ORCHESTRATION_PIPELINES_DAGS_DIRECTORY}/{bundle_name}"
    )
    dag_dest = f"gs://{composer_bucket}/{bundle_dag_prefix}/{dag_path.name}"

    if not pipeline_path.exists():
      raise calliope_exceptions.BadFileException(
          f"{pipeline_path.name} not found in {bundle_dir}"
      )

    try:
      yaml_content = files.ReadFileContents(pipeline_path)
    except files.Error as e:
      raise calliope_exceptions.BadFileException(
          f"Error reading {pipeline_path.name}: {e}"
      )

    resolved_pipeline = yaml_processor.resolve_dynamic_variables(
        yaml_content=yaml_content,
        combined_variables=combined_variables,
        deployment=parsed_deployment,
    )

    if rollback and _ArtifactsExist(artifact_base_uri):
      log.status.Print(
          f"Rollback optimization: Artifacts for version {version_id} "
          "already found in GCS. Skipping build and upload."
      )
    else:
      self._ProcessAndUploadArtifacts(
          resolved_pipeline,
          bundle_dir,
          composer_bucket,
          bundle_data_prefix,
          version_id,
          artifact_base_uri,
      )

    resolved_yaml_content = yaml.dump(resolved_pipeline)
    safe_name = pipeline_path.stem + ".yml"
    yaml_dest = f"gs://{composer_bucket}/{bundle_data_prefix}/versions/{version_id}/{safe_name}"
    dag_content = DAG_TEMPLATE.format(bundle_id=bundle_name)

    _UploadFile(
        dag_content,
        dag_dest,
        dag_path.name,
    )
    _UploadFile(
        resolved_yaml_content,
        yaml_dest,
        pipeline_path.name,
    )

    self._UpdateManifest(
        composer_bucket,
        bundle_data_prefix,
        version_id,
        git_context_obj,
        pipeline_path,
        bundle_name,
        is_paused=is_paused,
        is_local=is_local,
    )

    return version_id

  def _UploadArtifacts(
      self,
      *,
      work_dir: pathlib.Path,
      artifact_uri: str,
      action_filenames: set[str] | None = None,
      env_pack_files: set[str] | None = None,
  ) -> None:
    """Uploads pipeline artifacts to the GCS artifact bucket."""
    storage_client = storage_api.StorageClient()

    if env_pack_files:
      for env_file in env_pack_files:
        env_pack_path = work_dir / env_file
        if env_pack_path.exists():
          dest_ref = storage_util.ObjectReference.FromUrl(
              f"{artifact_uri}{env_file}"
          )
          storage_client.CopyFileToGCS(str(env_pack_path), dest_ref)
          env_pack_path.unlink()

    if action_filenames:
      for filename in action_filenames:
        if filename.startswith("gs://"):
          continue

        clean_path = _GetRelativePath(filename)
        local_path = work_dir / clean_path
        if not local_path.exists():
          log.warning(
              f"Action file not found locally, skipping upload: {local_path}"
          )
          continue

        dest_uri = f"{artifact_uri}{clean_path}"
        log.status.Print(
            f"Uploading action file '{clean_path}' to artifacts bucket..."
        )

        if local_path.is_dir():
          _UploadDirToGcs(local_path, dest_uri)
        else:
          dest_ref = storage_util.ObjectReference.FromUrl(dest_uri)
          storage_client.CopyFileToGCS(str(local_path), dest_ref)

    init_action_path = work_dir / "python_environment_unpack.sh"
    if init_action_path.exists():
      dest_ref = storage_util.ObjectReference.FromUrl(
          f"{artifact_uri}python_environment_unpack.sh"
      )
      storage_client.CopyFileToGCS(str(init_action_path), dest_ref)
      log.debug("Copied init action to %s", artifact_uri)
      init_action_path.unlink()
