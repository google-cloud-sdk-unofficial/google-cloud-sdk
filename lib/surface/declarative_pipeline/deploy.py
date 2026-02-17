# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Deploy command for declarative pipelines."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pathlib
import subprocess
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.declarative_pipeline import deployment_model
from googlecloudsdk.command_lib.declarative_pipeline import gcp_deployer
from googlecloudsdk.command_lib.declarative_pipeline.handlers import dataproc
from googlecloudsdk.command_lib.declarative_pipeline.processors import action_processor
from googlecloudsdk.command_lib.declarative_pipeline.tools import yaml_processor
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

DAG_FILE_NAME = "orchestration-pipeline.py"
PIPELINE_FILE = "orchestration-pipeline.yaml"
MANIFEST_FILE_NAME = "manifest.yml"
ENV_PACK_FILE = "environment.tar.gz"


class DeployError(exceptions.Error):
  """Exception for errors during the deploy process."""
  pass


def _CheckGitStatus(subprocess_mod):
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
        log.error(f"Uncommitted changes detected!\n{real_changes!r}")
        raise DeployError(
            "Please commit or stash changes before deploying."
        )
  except subprocess_mod.CalledProcessError as e:
    raise calliope_exceptions.FailedSubCommand(e.cmd, e.returncode)


def _GetVersionId(subprocess_mod):
  """Gets the current git commit hash as the version ID."""
  try:
    return (
        subprocess_mod.check_output(["git", "rev-parse", "HEAD"])
        .decode("utf-8")
        .strip()
    )
  except (subprocess_mod.CalledProcessError, FileNotFoundError):
    raise DeployError(textwrap.dedent("""
        Please ensure command is run from within a git repository."""))


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
    log.error(f"GCS Operation Failed: {e.stderr}")
    raise DeployError(
        f"GCS Upload failed. Check the error: {e}"
    ) from e


def _UploadString(subprocess_mod, content, dest):
  """Streams a string to GCS and reports errors."""
  with subprocess_mod.Popen(
      ["gcloud", "storage", "cp", "-", dest],
      stdin=subprocess_mod.PIPE,
      stdout=subprocess_mod.PIPE,
      stderr=subprocess_mod.PIPE,
  ) as p:
    _, stderr = p.communicate(input=content.encode("utf-8"))
    if p.returncode != 0:
      log.error(f"Failed to upload pipeline yaml to {dest}: {stderr.decode()}")
      raise DeployError("pipeline yaml upload to GCS failed.")


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
        f"from file '{deployment_file.name}'."
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
  else:
    raise DeployError(f"Unsupported resource type: {resource.type}")


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.GA)
class Deploy(calliope_base.Command):
  """Deploy a declarative pipeline."""

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

  def Run(self, args):
    work_dir = pathlib.Path.cwd()
    status = {
        "resource_deployment": "SKIPPED",
        "pipeline_deployment": "SKIPPED",
    }
    did_work = False

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
      for resource in deployment.environments[args.env].resources:
        if resource.type == "resourceProfile":
          pipeline_path = work_dir / PIPELINE_FILE
          version_id = self._DeployPipeline(
              args, work_dir, pipeline_path, deployment_path
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

  def _DeployPipeline(self, args, work_dir, pipeline_path, deployment_path):
    """Deploys the pipeline using the dynamic context."""
    _CheckGitStatus(self._subprocess)
    version_id = _GetVersionId(self._subprocess)

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
    _UploadString(self._subprocess, resolved_yaml_content, yaml_dest)

    dag_path = work_dir / DAG_FILE_NAME
    if dag_path.exists():
      _RunGcloudStorage(
          self._subprocess,
          ["cp", str(dag_path), f"gs://{composer_bucket}/dags/{DAG_FILE_NAME}"],
      )

    manifest_dest = (
        f"gs://{composer_bucket}/data/{pipeline_id}/{MANIFEST_FILE_NAME}"
    )
    _UploadString(
        self._subprocess, f"default-version: {version_id}", manifest_dest
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
          ["cp", "-r", str(jobs_dir / "*.py"), artifact_uri + "jobs/"],
      )
