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

import datetime
import getpass
import json
import os
import pathlib
import re
import subprocess

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines import gcp_deployer
from googlecloudsdk.command_lib.orchestration_pipelines import git_context
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import bq
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import bq_dts
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import composer
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import dataform
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import dataproc
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import iam
from googlecloudsdk.command_lib.orchestration_pipelines.processors import action_processor
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

DEPLOYMENT_FILE = "deployment.yaml"
MANIFEST_FILE_NAME = "manifest.yml"
ENV_PACK_FILE = "environment.tar.gz"

# Auto-generated DAG boilerplate
DAG_TEMPLATE = (
    """\"\"\"Generates a Composer DAG from a declarative pipeline definition.

This script reads pipeline configuration from YAML files located in a 'data'
folder, based on a manifest file, and uses it to generate an Airflow DAG
using `composer_declarative_dags`.
\"\"\"

import os
import pathlib
from pathlib import Path

from declarative_pipelines_lib.api import generate_dag
"""
    + "import yaml"
    + """

Path = pathlib.Path
MANIFEST_FILE_NAME = "manifest.yml"
ORCHESTRATION_PIPELINES_DIR = "orchestration_pipelines"


def _get_definition_file_path():
  \"\"\"Reads the pipeline definition from the GCS /data folder relative to the DAG.\"\"\"

  # 1. Identify where we are:
  # {gcs_root}/dags/declarative_pipelines/{bundle_name}/orchestration-pipeline.py
  current_file_path = Path(__file__).resolve()
  bundle_name = current_file_path.parent.name
  pipeline_filename = current_file_path.stem

  # 2. Navigate to the GCS root (usually /home/airflow/gcs/)
  # Moving up 3 levels: {bundle_name} -> declarative_pipelines -> dags
  gcs_root = current_file_path.parents[3]
  data_dir = gcs_root / "data"

  # 3. Locate the manifest in
  # /data/declarative_pipelines/{bundle_name}/manifest.yaml
  manifest_path = (
      data_dir / ORCHESTRATION_PIPELINES_DIR / bundle_name / MANIFEST_FILE_NAME
  )

  if not manifest_path.exists():
    raise FileNotFoundError(f"Manifest not found at: {manifest_path}")

  # Use read_text() to bypass gcloud CLI linters
  manifest_data = yaml.safe_load(manifest_path.read_text(encoding='utf-8'))
  version_id = manifest_data.get("default-version")
  if not version_id:
    raise ValueError(f"No 'default-version' in {manifest_path}")

  # 4. Locate the version-specific YAML
  # /data/declarative_pipelines/{bundle_name}/versions/{versionid}/orchestration-pipeline.yaml
  config_path = (
      data_dir
      / ORCHESTRATION_PIPELINES_DIR
      / bundle_name
      / "versions"
      / str(version_id)
      / f"{pipeline_filename}.yaml"
  )

  if not config_path.exists():
    raise FileNotFoundError(f"Pipeline config not found at: {config_path}")

  return config_path


def define():
  pipeline_definition_path = _get_definition_file_path()
  # Use read_text() to bypass gcloud CLI linters
  definition = yaml.safe_load(pipeline_definition_path.read_text(encoding='utf-8'))
  return generate_dag(definition)


dag = define()
"""
)


class DeployError(exceptions.Error):
  """Exception for errors during the deploy process."""
  pass


def _CollectEnvironmentVariables():
  """Collects variables from environment variables with _DEPLOY_VAR_ prefix."""
  env_vars = {}
  for key, value in os.environ.items():
    if key.startswith("_DEPLOY_VAR_"):
      env_vars[key[len("_DEPLOY_VAR_") :]] = value
  return env_vars


def _GetRepoName(subprocess_mod):
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


def _GetComposerBucket(subprocess_mod, env_name, location):
  """Retrieves the GCS bucket for the Composer environment."""
  try:
    out = subprocess_mod.check_output(
        [
            "gcloud",
            "composer",
            "environments",
            "describe",
            env_name,
            "--location",
            location,
            "--format",
            "value(config.dagGcsPrefix)",
        ],
        text=True,
    ).strip()
    if not out:
      raise DeployError(
          f"Failed to retrieve Composer bucket from environment '{env_name}'."
          " Ensure the environment exists and is fully initialized."
      )
    bucket = out.replace("gs://", "").split("/")[0]
    return bucket
  except subprocess_mod.CalledProcessError as e:
    raise DeployError(f"Failed to find Composer bucket: {e}") from e


def _RunGcloudStorage(subprocess_mod, args):
  """Runs gcloud storage commands and captures errors."""
  try:
    subprocess_mod.run(
        ["gcloud", "storage"] + args,
        capture_output=True,
        text=True,
        check=True,
    )
  except subprocess_mod.CalledProcessError as e:
    log.error("GCS Operation Failed: %s", e.stderr)
    raise DeployError(
        f"GCS Upload failed. Check the error: {e}"
    ) from e


def _UploadFile(
    subprocess_mod, content, dest, file_name, if_generation_match=None
):
  """Uploads files to GCS, optionally with optimistic locking."""

  cmd = ["gcloud", "storage", "cp", "-", dest]

  if if_generation_match is not None:
    cmd.append(f"--if-generation-match={if_generation_match}")

  with subprocess_mod.Popen(
      cmd,
      stdin=subprocess_mod.PIPE,
      stdout=subprocess_mod.PIPE,
      stderr=subprocess_mod.PIPE,
      text=True,
  ) as p:
    _, stderr = p.communicate(input=content)

    if p.returncode != 0:
      if "PreconditionFailed" in stderr or "412" in stderr:
        raise calliope_exceptions.HttpException(
            "Precondition Failed (Optimistic Lock Mismatch)"
        )
      log.error("Failed to upload %s to %s: %s", file_name, dest, stderr)
      raise DeployError("File upload to GCS failed.")


def _FetchManifest(subprocess_mod, bucket, manifest_dir_path):
  """Fetches manifest content and its GCS generation ID from a specific path."""
  manifest_path = f"gs://{bucket}/{manifest_dir_path}/{MANIFEST_FILE_NAME}"

  # 1. Get Generation ID (Metadata)
  try:
    meta_out = subprocess_mod.check_output(
        [
            "gcloud",
            "storage",
            "objects",
            "describe",
            manifest_path,
            "--format=json",
        ],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()
    metadata = json.loads(meta_out)
    generation = metadata.get("generation")
  except subprocess_mod.CalledProcessError:
    return None, 0

  # 2. Get Content
  try:
    content_out = subprocess_mod.check_output(
        ["gcloud", "storage", "cp", manifest_path, "-"],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()
    return yaml.load(content_out), generation
  except subprocess_mod.CalledProcessError:
    return None, 0


def _NormalizeArtifactPath(path):
  """Normalizes artifact path to be either absolute or gs path."""
  if path and isinstance(path, str):
    if not path.startswith("gs://") and not path.startswith("/"):
      path = "/" + (path[2:] if path.startswith("./") else path)
  return path


def _GetRelativePath(path):
  """Returns path relative to bundle dir, removing leading '/' and './'."""
  path = path.lstrip("/")
  if path.startswith("./"):
    path = path[2:]
  return path


def _DeployGcpResources(deployment_file, env, dry_run, external_vars=None):
  """Deploys GCP resources based on a deployment file.

  Args:
    deployment_file: The path to the deployment definition file.
    env: The target environment for the deployment.
    dry_run: If True, performs a dry run.
    external_vars: Optional dict of external variables to substitute.

  Raises:
    DeployError: If the specified environment is not found in the
      deployment file, or if any error occurs during the resource deployment
      process.

  Returns:
    The number of resources deployed.
  """
  log.status.Print(
      f"Deployment file {deployment_file.name} found, deploying resources..."
  )
  resources_deployed_count = 0
  try:
    # Load environment with variable substitution
    environment = yaml_processor.load_environment(
        deployment_file, env, external_vars
    )
    yaml_processor.validate_environment(environment, env)

    for resource in environment.resources:
      if resource.type == "resourceProfile":
        log.status.Print(f"Skipping resource profile '{resource.name}'.")
        continue
      handler = _GetHandler(resource, environment, dry_run)
      gcp_deployer.deploy_gcp_resource(handler)
      resources_deployed_count += 1
  except Exception as e:
    raise DeployError(
        f"Failed to deploy resources for environment '{env}' "
        f"from file '{deployment_file.name}':\n{e}"
    ) from e
  return resources_deployed_count


_RESOURCE_HANDLERS = {
    "dataproc.cluster": dataproc.DataprocClusterHandler,
    "bigquerydatatransfer.transferConfig": bq_dts.BqDataTransferConfigHandler,
    "dataform.repository": dataform.DataformRepositoryHandler,
    "dataform.repository.releaseConfig": dataform.DataformReleaseConfigHandler,
    "dataform.repository.workflowConfig": (
        dataform.DataformWorkflowConfigHandler
    ),
    "bigquery.dataset": bq.BqDatasetHandler,
    "bigquery.table": bq.BqTableHandler,
    "composer.environment": composer.ComposerEnvironmentHandler,
    "iam.serviceAccount": iam.IamServiceAccountHandler,
}


def _GetHandler(
    resource, environment, dry_run, *, debug=False, show_requests=False
):
  """Gets the appropriate handler for a given resource.

  Args:
    resource: The resource object from the deployment model.
    environment: The environment object from the deployment model.
    dry_run: Whether to perform a dry run.
    debug: Whether to enable debug logging.
    show_requests: Whether to show API requests.

  Returns:
    A handler object for the specified resource type.

  Raises:
    DeployError: If the resource type is not supported.
  """
  handler_class = _RESOURCE_HANDLERS.get(resource.type)
  if not handler_class:
    raise DeployError(f"Unsupported resource type: {resource.type}")

  return handler_class(resource, environment, dry_run, debug, show_requests)


def _ArtifactsExist(subprocess_mod, artifact_uri):
  """Checks if artifacts already exist in GCS (optimization for rollbacks)."""
  try:
    subprocess_mod.check_call(
        ["gcloud", "storage", "ls", artifact_uri],
    )
    return True
  except subprocess_mod.CalledProcessError:
    return False


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class Deploy(calliope_base.Command):
  """Deploy a pipeline."""

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._subprocess = subprocess

  @staticmethod
  def Args(parser):
    parser.add_argument(
        "--environment",
        required=True,
        choices=["dev", "stage", "prod"],
        help="The target environment for the deployment.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, performs a dry run of the deployment.",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="If set, performs a rollback to a specified version.",
    )
    parser.add_argument(
        "--version",
        help=(
            "The git SHA version to rollback to. Required if --rollback is set."
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
            "Particularly useful for speeding up --local deployments."
        ),
    )

  def Run(self, args):
    work_dir = pathlib.Path.cwd()
    status = {
        "resource_deployment": "SKIPPED",
        "pipeline_deployment": "SKIPPED",
    }
    external_vars = _CollectEnvironmentVariables()
    explicit_version = None

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
      if args.environment == "prod" or args.environment == "stage":
        raise DeployError(
            "Invalid Arguments: --local mode is not available for prod "
            "environment. Please use dev environment."
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
      resources_deployed_count = _DeployGcpResources(
          deployment_path, args.environment, args.dry_run, external_vars
      )
      if resources_deployed_count > 0:

        status["resource_deployment"] = "SUCCESS"
      else:
        status["resource_deployment"] = "SKIPPED"
    except (yaml.FileLoadError, yaml.YAMLParseError) as e:
      raise calliope_exceptions.BadFileException(
          "Deployment file not found or failed to parse: "
          f"{deployment_path.name}"
      ) from e
    parsed_deployment = yaml_processor.parse_deployment(
        deployment_path, args.environment, external_vars
    )
    pipelines = parsed_deployment.get("pipelines", [])
    if getattr(args, "pipeline", None):
      filtered_pipelines = []
      for p in pipelines:

        if args.pipeline == p.source:
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
    for pipeline in pipelines:
      yaml_path = bundle_dir / pipeline.source

      version_id = self._DeployPipeline(
          args,
          bundle_dir,
          yaml_path,
          deployment_path,
          git_context_obj,
          rollback=args.rollback,
          bundle_name=bundle_name,
          external_vars=external_vars,
      )
      status["pipeline_deployment"] = "SUCCESS"
      status["version"] = version_id
    success_states = ["SUCCESS"]
    if (
        status["resource_deployment"] not in success_states
        and status["pipeline_deployment"] not in success_states
    ):
      raise DeployError(
          f"Failed to deploy. Searched recursively in {work_dir}, but found no"
          " valid bundles containing both a pipeline YAML (with pipelineId)"
          f" and a {DEPLOYMENT_FILE} for environment '{args.environment}'."
      )

    if (
        status["pipeline_deployment"] == "SUCCESS"
        and status["resource_deployment"] == "SUCCESS"
    ):
      log.status.Print(
          "Resource and pipeline deployment successful for version"
          f" {status['version']}"
      )
    elif status["pipeline_deployment"] == "SUCCESS":
      log.status.Print(
          f"Pipeline deployment successful for version {status['version']}"
      )
    elif status["resource_deployment"] == "SUCCESS":
      log.status.Print("Resource deployment successful.")

  def _ProcessAndUploadArtifacts(
      self,
      resolved_pipeline,
      bundle_dir,
      composer_bucket,
      bundle_dag_prefix,
      artifact_base_uri,
  ):
    """Processes actions and uploads artifacts to GCS."""
    uploaded_dag_projects = set()
    action_filenames_to_upload = set()

    for action in resolved_pipeline.get("actions", []):
      filename = action.get("filename")
      if filename and isinstance(filename, str):
        filename = _NormalizeArtifactPath(filename)
        action["filename"] = filename
        action_filenames_to_upload.add(filename)

      clean_path = action.pop("_local_dag_upload_path", None)
      if clean_path and clean_path not in uploaded_dag_projects:
        uploaded_dag_projects.add(clean_path)
        local_project_path = bundle_dir / clean_path

        if local_project_path.exists() and local_project_path.is_dir():
          dags_dest_uri = (
              f"gs://{composer_bucket}/{bundle_dag_prefix}/{clean_path}/"
          )

          engine_raw = action.get("engine")
          engine_str = (
              engine_raw.get("engineType")
              if isinstance(engine_raw, dict)
              else engine_raw
          )

          log.status.Print(
              f"Uploading {engine_str.upper()} project '{clean_path}' to"
              " DAGs folder..."
          )
          _RunGcloudStorage(
              self._subprocess,
              ["cp", "-r", str(local_project_path / "*"), dags_dest_uri],
          )
        else:
          log.warning(f"Project path not found locally: {clean_path}")
      processor = action_processor.get_action_processor(
          action,
          bundle_dir,
          artifact_base_uri,
          # TODO(b/474620155): This should per action, not global.
          ENV_PACK_FILE,
          self._subprocess,
          resolved_pipeline.get("defaults", {}),
      )
      processor.process_action()

    self._UploadArtifacts(
        subprocess_mod=self._subprocess,
        work_dir=bundle_dir,
        artifact_uri=artifact_base_uri,
        action_filenames=action_filenames_to_upload,
    )

  def _UpdateManifest(
      self,
      composer_bucket,
      bundle_data_prefix,
      version_id,
      git_context_obj,
      environment,
      rollback,
      pipeline_path,
  ):
    """Updates the manifest file in GCS with retry logic."""
    manifest_dest = (
        f"gs://{composer_bucket}/{bundle_data_prefix}/{MANIFEST_FILE_NAME}"
    )
    max_retries = 5
    attempts = 0

    while attempts < max_retries:
      manifest_data, read_generation_id = _FetchManifest(
          self._subprocess, composer_bucket, bundle_data_prefix
      )
      if manifest_data is None:
        manifest_data = {}

      bypass = rollback
      remote_version = git_context_obj.ValidateAncestryOrRaise(
          manifest_data.get("default-version"),
          environment,
          bypass=bypass,
      )
      # TODO(b/474163740): Remove version fields updates below once composer
      # team changes are ready.
      prev_version = manifest_data.get("prev-version", [])
      if remote_version and (
          not prev_version or prev_version[-1] != remote_version
      ):
        prev_version.append(remote_version)

      new_manifest_payload = {
          "default-version": str(version_id),
          "prev-version": prev_version,
          "timestamp": datetime.datetime.now().isoformat(),
          "prev-gcs-version": str(read_generation_id),
      }

      try:
        log.status.Print(
            "Attempting to update manifest (Generation match:"
            f" {read_generation_id})..."
        )
        _UploadFile(
            self._subprocess,
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
      args,
      bundle_dir,
      pipeline_path,
      deployment_path,
      git_context_obj,
      rollback=False,
      bundle_name=None,
      external_vars=None,
  ):
    """Deploys the pipeline using the dynamic context and concurrency control.

    Args:
      args: The parsed command-line arguments.
      bundle_dir: The directory containing the pipeline bundle.
      pipeline_path: The path to the pipeline YAML file.
      deployment_path: The path to the deployment YAML file.
      git_context_obj: The GitContext object.
      rollback: If True, this is a rollback operation.
      bundle_name: The name of the bundle.
      external_vars: Optional dict of external variables to substitute.

    Returns:
      The version ID (git commit hash) of the deployed pipeline.

    Raises:
      calliope_exceptions.BadFileException: If the pipeline file is not found
        or cannot be read.
      DeployError: If the manifest update fails after multiple retries.
    """
    git_context_obj.EnforceClean()
    version_id = git_context_obj.CalculateVersionId()

    parsed_deployment = yaml_processor.parse_deployment(
        deployment_path, args.environment, external_vars
    )
    composer_bucket = _GetComposerBucket(
        self._subprocess,
        parsed_deployment["composer_env"],
        parsed_deployment["region"],
    )
    bundle_data_prefix = f"data/orchestration_pipelines/{bundle_name}"
    artifact_base_uri = (
        f"gs://{parsed_deployment['artifact_storage']['bucket']}/"
        f"{parsed_deployment['artifact_storage']['path_prefix']}/"
        f"{bundle_dir.name}/versions/{version_id}/"
    )
    dag_path = pipeline_path.with_suffix(".py")
    bundle_dag_prefix = f"dags/orchestration_pipelines/{bundle_name}"
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
        deployment_path=deployment_path,
        env=args.environment,
        external_variables=external_vars,
        bundle_dag_prefix=bundle_dag_prefix,
    )

    if rollback and _ArtifactsExist(self._subprocess, artifact_base_uri):
      log.status.Print(
          f"Rollback optimization: Artifacts for version {version_id} "
          "already found in GCS. Skipping build and upload."
      )
    else:
      self._ProcessAndUploadArtifacts(
          resolved_pipeline,
          bundle_dir,
          composer_bucket,
          bundle_dag_prefix,
          artifact_base_uri,
      )

    resolved_yaml_content = yaml.dump(resolved_pipeline)
    yaml_dest = f"gs://{composer_bucket}/{bundle_data_prefix}/versions/{version_id}/{pipeline_path.name}"
    _UploadFile(
        self._subprocess,
        resolved_yaml_content,
        yaml_dest,
        pipeline_path.name,
    )

    _UploadFile(
        self._subprocess,
        DAG_TEMPLATE,
        dag_dest,
        dag_path.name,
    )

    self._UpdateManifest(
        composer_bucket,
        bundle_data_prefix,
        version_id,
        git_context_obj,
        args.environment,
        rollback,
        pipeline_path,
    )

    return version_id

  def _UploadArtifacts(
      self,
      *,
      subprocess_mod,
      work_dir,
      artifact_uri,
      action_filenames=None,
  ):
    """Uploads pipeline artifacts to the GCS artifact bucket."""
    env_pack_path = work_dir / ENV_PACK_FILE
    if env_pack_path.exists():
      _RunGcloudStorage(
          subprocess_mod, ["cp", str(env_pack_path), artifact_uri]
      )
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
          _RunGcloudStorage(
              subprocess_mod, ["cp", "-r", str(local_path / "*"), dest_uri]
          )
        else:
          _RunGcloudStorage(subprocess_mod, ["cp", str(local_path), dest_uri])

    init_action_path = work_dir / "python_environment_unpack.sh"
    if init_action_path.exists():
      _RunGcloudStorage(
          subprocess_mod, ["cp", str(init_action_path), artifact_uri]
      )
      log.debug("Copied init action to %s", artifact_uri)
      init_action_path.unlink()
