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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import json
import pathlib
import subprocess
import textwrap
import time

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines import deployment_model
from googlecloudsdk.command_lib.orchestration_pipelines import gcp_deployer
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import bq_dts
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import dataform
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import dataproc
from googlecloudsdk.command_lib.orchestration_pipelines.processors import action_processor
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files

DAG_FILE_NAME = "orchestration-pipeline.py"
PIPELINE_FILE = "orchestration-pipeline.yaml"
MANIFEST_FILE_NAME = "manifest.yml"
ENV_PACK_FILE = "environment.tar.gz"


class DeployError(exceptions.Error):
  """Exception for errors during the deploy process."""
  pass


def _CheckGitStatus(subprocess_mod, force=False):
  """Checks if there are uncommitted changes in the git repository."""
  try:
    status_output = subprocess_mod.check_output(
        ["git", "status", "--porcelain"], text=True
    ).strip()
    if status_output:
      lines = status_output.splitlines()
      ignored_patterns = [".pyc", "__pycache__", ENV_PACK_FILE]
      real_changes = [
          l for l in lines if not any(p in l for p in ignored_patterns)
      ]
      if real_changes:
        formatted_changes = "\n".join([f"  - {l}" for l in real_changes])
        msg = "Uncommitted changes detected!\n%r", formatted_changes
        if force:
          msg_lines = [
              "Uncommitted changes detected:",
              *[f"  - {l}" for l in real_changes],
              "",
              "Using --force will proceed with these changes:",
              (
                  "- During a rollback, these local changes will be permanently"
                  " lost."
              ),
              (
                  "- During a standard deployment, your uploaded code will not"
                  " match your Git history."
              ),
          ]
          warning_msg = "\n".join(msg_lines)
          log.warning(warning_msg)

          console_io.PromptContinue(
              message="Are you sure you want to proceed?",
              default=False,
              cancel_on_no=True,
          )

          log.warning("FORCE MODE: Proceeding with uncommitted changes.")
          return
        log.error(msg)
        raise DeployError(
            "Please commit or stash changes before deploying, or use --force."
        )
  except subprocess_mod.CalledProcessError as e:
    raise calliope_exceptions.FailedSubCommand(e.cmd, e.returncode)


def _GetVersionId(subprocess_mod, force=False, version_override=None):
  """Gets the version ID, using override or current git commit hash."""
  if version_override:
    sha = version_override
  else:
    try:
      sha = (
          subprocess_mod.check_output(["git", "rev-parse", "HEAD"])
          .decode("utf-8")
          .strip()
      )
    except (subprocess_mod.CalledProcessError, FileNotFoundError):
      raise DeployError(textwrap.dedent("""
          Please ensure command is run from within a git repository."""))
  if force and not version_override:
    timestamp = int(time.time())
    sha = f"{sha}-forced-{timestamp}"
  return sha


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


def _FetchManifest(subprocess_mod, bucket, pipeline_id):
  """Fetches manifest content and its GCS generation ID."""
  manifest_path = f"gs://{bucket}/data/{pipeline_id}/{MANIFEST_FILE_NAME}"

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


def _CheckAncestry(subprocess_mod, remote_sha, local_sha, env):
  """Verifies that the remote version is an ancestor of the local version.

  Args:
    subprocess_mod: The subprocess module or a mock for testing.
    remote_sha: The git commit hash of the remote version.
    local_sha: The git commit hash of the local version.
    env: The target environment for the deployment.

  Returns:
    True if the remote_sha is an ancestor of local_sha, or if the check is
    skipped (e.g., in 'dev' environment or if remote_sha is not found). False
    otherwise.
  """
  if not remote_sha:
    return True

  # Strip '-forced-...' suffix if present to get the clean SHA for git checks
  clean_local_sha = local_sha.split("-forced-")[0]
  clean_remote_sha = str(remote_sha).split("-forced-")[0]

  try:
    subprocess_mod.check_call(
        ["git", "cat-file", "-t", clean_remote_sha],
    )
  except subprocess_mod.CalledProcessError:
    if env == "dev":
      log.warning(
          "Remote version %s unknown locally. Proceeding (DEV mode).",
          remote_sha,
      )
      return True
    log.error("Remote version %s not found in local git history.", remote_sha)
    return False

  try:
    subprocess_mod.check_call(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            clean_remote_sha,
            clean_local_sha,
        ],
    )
    return True
  except subprocess_mod.CalledProcessError:
    if env == "dev":
      log.warning(
          "Remote %s is not an ancestor of %s. Proceeding (DEV mode).",
          remote_sha,
          local_sha,
      )
      return True
    return False


def _ValidateAncestryOrRaise(
    subprocess_mod, manifest_data, local_version, env, bypass_ancestry=False
):
  """Validates that the remote version in the manifest is safe to overwrite.

  Args:
    subprocess_mod: The subprocess module or a mock for testing.
    manifest_data: The parsed content of the manifest file from GCS, or None.
    local_version: The current local git commit hash.
    env: The target environment for the deployment.
    bypass_ancestry: If True, skips the ancestry check (rollbacks/force).

  Returns:
      The remote_version string if safe (or None if no manifest exists).

  Raises:
      DeployError: If the remote version is ahead of the local version.
  """
  if not manifest_data:
    return None

  remote_version = manifest_data.get("default-version")

  if bypass_ancestry:
    log.status.Print(
        f"Bypassing ancestry check for remote version {remote_version}."
    )
    return remote_version

  if not _CheckAncestry(subprocess_mod, remote_version, local_version, env):
    raise DeployError(
        f"REGRESSION BLOCKED: The remote version ({remote_version}) "
        f"is ahead of or divergent from your local version ({local_version}).\n"
        "Please 'git pull' the latest changes before deploying."
    )

  return remote_version


def _DeployGcpResources(deployment_file, env, dry_run):
  """Deploys GCP resources based on a deployment file.

  Args:
    deployment_file: The path to the deployment definition file.
    env: The target environment for the deployment.
    dry_run: If True, performs a dry run.

  Raises:
    DeployError: If the specified environment is not found in the
      deployment file, or if any error occurs during the resource deployment
      process.
  """
  log.status.Print(
      f"Deployment file {deployment_file.name} found, deploying resources..."
  )
  try:
    deployment_config = yaml.load_path(str(deployment_file))
    deployment = deployment_model.DeploymentModel.build(deployment_config)
    # TODO(b/474163740): Remove this check once the validation is ready.
    if env not in deployment.environments:
      raise DeployError(
          f'Environment "{env}" not found in {deployment_file.name}'
      )
    environment = deployment.environments[env]
    for resource in environment.resources:
      if resource.type == "resourceProfile":
        log.status.Print(f"Skipping resource profile '{resource.name}'.")
        continue
      handler = _GetHandler(resource, environment, dry_run)
      gcp_deployer.deploy_gcp_resource(handler)
  except Exception as e:
    raise DeployError(
        f"Failed to deploy resources for environment '{env}' "
        f"from file '{deployment_file.name}':\n{e}"
    ) from e


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
  if resource.type == "dataproc.cluster":
    return dataproc.DataprocClusterHandler(
        resource, environment, dry_run, debug, show_requests
    )
  if resource.type == "bigquery.datatransfer.config":
    return bq_dts.BqDataTransferConfigHandler(
        resource, environment, dry_run, debug, show_requests
    )
  if resource.type == "dataform.repository":
    return dataform.DataformRepositoryHandler(
        resource, environment, dry_run, debug, show_requests
    )
  if resource.type == "dataform.repository.releaseConfig":
    return dataform.DataformReleaseConfigHandler(
        resource, environment, dry_run, debug, show_requests
    )
  if resource.type == "dataform.repository.workflowConfig":
    return dataform.DataformWorkflowConfigHandler(
        resource, environment, dry_run, debug, show_requests
    )
  else:
    raise DeployError(f"Unsupported resource type: {resource.type}")


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
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.GA)
class Deploy(calliope_base.Command):
  """Deploy a pipeline."""

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._subprocess = subprocess

  @staticmethod
  def Args(parser):
    parser.add_argument(
        "--env",
        required=True,
        choices=["dev", "stage", "prod"],
        help="The target environment for the deployment.",
    )
    parser.add_argument(
        "--deployment-file",
        help="The path to the deployment definition file.",
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
        "--force",
        action="store_true",
        help=(
            "Forces deployment, allowing uncommitted changes and bypassing "
            "ancestry checks."
        ),
    )

  def Run(self, args):
    work_dir = pathlib.Path.cwd()
    status = {
        "resource_deployment": "SKIPPED",
        "pipeline_deployment": "SKIPPED",
    }
    did_work = False
    version_to_deploy = None

    if args.rollback:
      if not args.version:
        raise calliope_exceptions.RequiredArgumentException(
            "--version", "Version (SHA) is required when --rollback is set."
        )
      _CheckGitStatus(self._subprocess, force=args.force)

      log.status.Print(
          f"Prepare Rollback: Checking out version {args.version}..."
      )
      try:
        checkout_cmd = ["git", "checkout", args.version]
        if args.force:
          checkout_cmd.append("--force")
        self._subprocess.check_call(checkout_cmd)
        version_to_deploy = args.version
      except subprocess.CalledProcessError as e:
        raise DeployError(
            f"Rollback failed: Could not rollback to version {args.version}. "
            f"Git error: {e}"
        )

    if args.deployment_file:
      deployment_path = work_dir / args.deployment_file
      deployment_yaml = yaml.load_path(str(deployment_path))
      deployment = deployment_model.DeploymentModel.build(deployment_yaml)
      try:
        _DeployGcpResources(deployment_path, args.env, args.dry_run)
        status["resource_deployment"] = "SUCCESS"
        did_work = True
      except (FileNotFoundError, yaml.YAMLParseError) as e:
        raise calliope_exceptions.BadFileException(
            "Deployment file not found or failed to parse: "
            f"{args.deployment_file}"
        ) from e
      if deployment.environments[args.env].composer_environment is not None:
        pipeline_path = work_dir / PIPELINE_FILE
        version_id = self._DeployPipeline(
            args,
            work_dir,
            pipeline_path,
            deployment_path,
            rollback=args.rollback,
            force=args.force,
            version_override=version_to_deploy,
        )
        status["pipeline_deployment"] = "SUCCESS"
        status["version"] = version_id
        did_work = True
        log.status.Print(
            f"Pipeline deployment successful for version {version_id}"
        )

    if not did_work:
      raise DeployError(
          "Nothing to deploy: resource deployment skipped (--deployment-file "
          "not provided) and pipeline deployment skipped "
          f"({PIPELINE_FILE} not found)."
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

  def _DeployPipeline(
      self,
      args,
      work_dir,
      pipeline_path,
      deployment_path,
      rollback=False,
      force=False,
      version_override=None,
  ):
    """Deploys the pipeline using the dynamic context and concurrency control.

    Args:
      args: The parsed command-line arguments.
      work_dir: The current working directory as a pathlib.Path.
      pipeline_path: The path to the pipeline YAML file.
      deployment_path: The path to the deployment YAML file.
      rollback: If True, this is a rollback operation.
      force: If True, force the deployment, bypassing some checks.
      version_override: Optional. A specific version ID to use.

    Returns:
      The version ID (git commit hash) of the deployed pipeline.

    Raises:
      calliope_exceptions.BadFileException: If the pipeline file is not found
        or cannot be read.
      DeployError: If the manifest update fails after multiple retries.
    """
    _CheckGitStatus(self._subprocess, force=force)
    version_id = _GetVersionId(
        self._subprocess, force=force, version_override=version_override
    )

    parsed_deployment = yaml_processor.parse_deployment(
        deployment_path, args.env
    )

    composer_bucket = _GetComposerBucket(
        self._subprocess,
        parsed_deployment["composer_env"],
        parsed_deployment["region"],
    )
    if not pipeline_path.exists():
      raise calliope_exceptions.BadFileException(
          f"{PIPELINE_FILE} not found in {work_dir}"
      )

    try:
      yaml_content = files.ReadFileContents(pipeline_path)
    except files.Error as e:
      raise calliope_exceptions.BadFileException(
          f"Error reading {PIPELINE_FILE}: {e}"
      )

    resolved_pipeline = yaml_processor.resolve_dynamic_variables(
        yaml_content=yaml_content,
        deployment_path=deployment_path,
        env=args.env,
    )

    artifact_base_path = f"{parsed_deployment['artifact_storage']['path_prefix']}/versions/{version_id}/"
    artifact_base_uri = f"gs://{parsed_deployment['artifact_storage']['bucket']}/{artifact_base_path}"
    pipeline_id = resolved_pipeline["pipelineId"]

    skip_artifact_upload = False

    if rollback and not force:
      if _ArtifactsExist(self._subprocess, artifact_base_uri):
        log.status.Print(
            f"Rollback optimization: Artifacts for version {version_id} "
            "already found in GCS. Skipping build and upload."
        )
        skip_artifact_upload = True

    if not skip_artifact_upload:
      for action in resolved_pipeline.get("actions", []):
        processor = action_processor.get_action_processor(
            action,
            work_dir,
            artifact_base_uri,
            # TODO(b/474620155): This should per action, not global.
            ENV_PACK_FILE,
            self._subprocess,
            resolved_pipeline.get("defaults", {}),
        )
        processor.process_action()

      self._UploadArtifacts(
          subprocess_mod=self._subprocess,
          work_dir=work_dir,
          artifact_uri=artifact_base_uri,
      )

    resolved_yaml_content = yaml.dump(resolved_pipeline)
    yaml_dest = (
        f"gs://{composer_bucket}/data/{pipeline_id}/"
        f"versions/{version_id}/{PIPELINE_FILE}"
    )
    _UploadFile(
        self._subprocess, resolved_yaml_content, yaml_dest, PIPELINE_FILE
    )

    dag_path = work_dir / DAG_FILE_NAME
    if dag_path.exists():
      _RunGcloudStorage(
          self._subprocess,
          ["cp", str(dag_path), f"gs://{composer_bucket}/dags/{DAG_FILE_NAME}"],
      )

    manifest_dest = (
        f"gs://{composer_bucket}/data/{pipeline_id}/{MANIFEST_FILE_NAME}"
    )

    max_retries = 5
    attempts = 0

    while attempts < max_retries:
      manifest_data, read_generation_id = _FetchManifest(
          self._subprocess, composer_bucket, pipeline_id
      )
      if manifest_data is None:
        manifest_data = {}

      bypass = rollback or force
      remote_version = _ValidateAncestryOrRaise(
          self._subprocess,
          manifest_data,
          version_id,
          args.env,
          bypass_ancestry=bypass,
      )
      # TODO(b/474163740): Remove version fields updates below once composer
      # team changes are ready.
      prev_version = manifest_data.get("prev-version", [])
      if remote_version:
        prev_version.append(remote_version)
      new_manifest_payload = {
          "default-version": version_id,
          "prev-version": prev_version,
          "timestamp": datetime.datetime.now().isoformat(),
          "prev-gcs-version": str(read_generation_id),
      }

      manifest_content_str = yaml.dump(new_manifest_payload)

      try:
        log.status.Print(
            "Attempting to update manifest (Generation match:"
            f" {read_generation_id})..."
        )

        _UploadFile(
            self._subprocess,
            manifest_content_str,
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
          "Failed to update manifest after multiple retries due to high"
          " concurrency."
      )

    return version_id

  def _UploadArtifacts(self, *, subprocess_mod, work_dir, artifact_uri):
    """Uploads pipeline artifacts to the GCS artifact bucket."""
    env_pack_path = work_dir / ENV_PACK_FILE
    if env_pack_path.exists():
      _RunGcloudStorage(
          subprocess_mod, ["cp", str(env_pack_path), artifact_uri]
      )

    jobs_dir = work_dir / "jobs"
    if jobs_dir.exists():
      _RunGcloudStorage(
          subprocess_mod,
          ["cp", "-r", str(jobs_dir / "*"), artifact_uri + "jobs/"],
      )
