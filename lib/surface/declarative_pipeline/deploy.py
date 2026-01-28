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

from collections.abc import MutableMapping, Sequence
import contextlib
import pathlib
import subprocess
import sys
import textwrap
from typing import Any

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.declarative_pipeline import deployment_model
from googlecloudsdk.command_lib.declarative_pipeline import gcp_deployer
from googlecloudsdk.command_lib.declarative_pipeline.handlers import dataproc
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

PIPELINE_ID = "customer-analytics-pipeline"
ARTIFACT_BUCKET_NAME = "project-dataproc-artifacts"
COMPOSER_ENV_NAME = "zhiwei-auto-deploy"
LOCATION = "us-central1"

DAG_FILE_NAME = "orchestration-pipeline.py"
TEMPLATE_FILE = "orchestration-pipeline.yaml"
MANIFEST_FILE_NAME = "manifest.yml"
ENV_PACK_FILE = "environment.tar.gz"


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
        raise exceptions.ToolException(
            "Please commit or stash changes before deploying."
        )
  except subprocess_mod.CalledProcessError:
    raise exceptions.ToolException("Failed to check Git status.")


def _GetVersionId(subprocess_mod):
  """Gets the current git commit hash as the version ID."""
  try:
    return (
        subprocess_mod.check_output(["git", "rev-parse", "HEAD"])
        .decode("utf-8")
        .strip()
    )
  except (subprocess_mod.CalledProcessError, FileNotFoundError):
    raise exceptions.ToolException(textwrap.dedent("""\
        Please ensure command is run from within a git repository."""))


def _GetComposerBucket(subprocess_mod, env_name):
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
            LOCATION,
            "--format",
            "value(config.dagGcsPrefix)",
        ],
        text=True,
    ).strip()
    bucket, *_ = out.replace("gs://", "").split("/")
    return bucket
  except subprocess_mod.CalledProcessError as e:
    raise exceptions.ToolException(
        f"Failed to find Composer bucket: {e}"
    ) from e


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
    raise exceptions.ToolException(
        "GCS Upload failed. Check the error above."
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
      log.error(f"Failed to upload string to {dest}: {stderr.decode()}")
      raise exceptions.ToolException("String upload to GCS failed.")


@contextlib.contextmanager
def _TempBuildDir(work_dir):
  """Context manager for a temporary build directory."""
  build_root = work_dir / "temp_build_libs"
  try:
    files.RmTree(build_root)
  except FileNotFoundError:
    pass
  build_root.mkdir(parents=True, exist_ok=True)
  try:
    yield build_root
  finally:
    try:
      files.RmTree(build_root)
    except FileNotFoundError:
      pass


def _BuildEnvLocal(subprocess_mod, work_dir):
  """Builds dependencies.tar.gz locally using pip and tar.

  Args:
    subprocess_mod: The subprocess module or mock.
    work_dir: The working directory as a pathlib.Path object.
  """

  requirements_file = work_dir / "jobs" / "requirements.txt"
  output_zip = work_dir / ENV_PACK_FILE

  with _TempBuildDir(work_dir) as build_root:
    site_packages = build_root / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)

    try:
      pip_cmd = [
          sys.executable,
          "-m",
          "pip",
          "install",
          "-r",
          str(requirements_file),
          "--target",
          str(site_packages),
          "--no-cache-dir",
          "--platform",
          "manylinux2014_x86_64",
          "--only-binary=:all:",
          "--implementation",
          "cp",
          "--python-version",
          "3.11",
          "--extra-index-url",
          "https://pypi.org/simple",
      ]

      subprocess_mod.check_call(pip_cmd)

      subprocess_mod.check_call(
          [
              "tar",
              "-czf",  # Create, Gzip, File
              str(output_zip),
              "--exclude=*.pyc",
              "--exclude=__pycache__",
              "site-packages",
          ],
          cwd=str(build_root),
      )

    except subprocess_mod.CalledProcessError as e:
      raise exceptions.ToolException(
          "Local build failed. Ensure pip and tar are installed."
      ) from e


def _GetNestedDict(
    d: MutableMapping[str, Any], keys: Sequence[str]
) -> MutableMapping[str, Any]:
  """Gets a nested dictionary from `d`, creating keys with empty dictionaries if they don't exist."""
  current = d
  for key in keys:
    current = current.setdefault(key, {})
  return current


def _DeployGcpResources(deployment_file, env, dry_run):
  """Deploys GCP resources based on a deployment file.

  Args:
    deployment_file: The path to the deployment definition file.
    env: The target environment for the deployment.
    dry_run: If True, performs a dry run.

  Raises:
    googlecloudsdk.calliope.exceptions.ToolException: If the specified
      environment is not found in the deployment file, or if any error occurs
      during the resource deployment process.
  """
  log.status.Print(
      f"Deployment file {deployment_file.name} found, deploying resources..."
  )
  try:
    deployment_config = yaml.load_path(str(deployment_file))
    deployment = deployment_model.DeploymentModel.build(deployment_config)
    if env not in deployment.environments:
      raise exceptions.ToolException(
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
    raise exceptions.ToolException(
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
    exceptions.ToolException: If the resource type is not supported.
  """
  if resource.type == "dataproc.cluster":
    return dataproc.DataprocClusterHandler(
        resource, environment, dry_run, debug, show_requests
    )
  else:
    raise exceptions.ToolException(
        f"Unsupported resource type: {resource.type}"
    )


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
      try:
        _DeployGcpResources(deployment_path, args.env, args.dry_run)
        status["resource_deployment"] = "SUCCESS"
        did_work = True
      except (FileNotFoundError, yaml.YAMLParseError) as e:
        raise exceptions.BadFileException(
            "Deployment file not found or failed to parse: "
            f"{args.deployment_file}"
        ) from e
    else:
      log.status.Print(
          "--deployment-file not provided, skipping resource deployment."
      )

    template_path = work_dir / TEMPLATE_FILE
    if template_path.exists():
      version_id = self._DeployPipeline(work_dir, template_path)
      status["pipeline_deployment"] = "SUCCESS"
      status["version"] = version_id
      did_work = True
    else:
      log.status.Print(
          f'Pipeline file "{TEMPLATE_FILE}" not found, '
          'skipping pipeline deployment.'
      )

    if not did_work:
      raise exceptions.ToolException(
          "Nothing to deploy: resource deployment skipped (--deployment-file "
          "not provided) and pipeline deployment skipped "
          f"({TEMPLATE_FILE} not found)."
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

    return status

  def _DeployPipeline(self, work_dir, template_path):
    """Deploys the pipeline defined in template_path."""
    _CheckGitStatus(self._subprocess)
    version_id = _GetVersionId(self._subprocess)
    composer_bucket = _GetComposerBucket(self._subprocess, COMPOSER_ENV_NAME)

    artifact_base_path = f"pipelines/{PIPELINE_ID}/versions/{version_id}/"
    artifact_base_uri = f"gs://{ARTIFACT_BUCKET_NAME}/{artifact_base_path}"

    resolved_pipeline = yaml.load_path(str(template_path))

    if (work_dir / "jobs" / "requirements.txt").exists():
      _BuildEnvLocal(self._subprocess, work_dir)

    for action in resolved_pipeline.get("actions", []):
      self._ProcessPipelineAction(action, work_dir, artifact_base_uri)

    self._UploadArtifacts(
        subprocess_mod=self._subprocess,
        work_dir=work_dir,
        artifact_uri=artifact_base_uri,
    )

    resolved_yaml_content = yaml.dump(resolved_pipeline)
    yaml_dest = (
        f"gs://{composer_bucket}/data/{PIPELINE_ID}/"
        f"versions/{version_id}/{TEMPLATE_FILE}"
    )
    _UploadString(self._subprocess, resolved_yaml_content, yaml_dest)

    dag_path = work_dir / DAG_FILE_NAME
    if dag_path.exists():
      _RunGcloudStorage(
          self._subprocess,
          [
              "cp",
              str(dag_path),
              f"gs://{composer_bucket}/dags/{DAG_FILE_NAME}",
          ],
      )

    manifest_dest = (
        f"gs://{composer_bucket}/data/{PIPELINE_ID}/{MANIFEST_FILE_NAME}"
    )
    _UploadString(
        self._subprocess, f"default-version: {version_id}", manifest_dest
    )
    return version_id

  def _ProcessPipelineAction(self, action, work_dir, artifact_base_uri):
    """Processes a single action in the pipeline, resolving local paths to GCS URIs."""
    if "filename" not in action:
      return

    raw_path = action["filename"]
    local_path = pathlib.Path(raw_path.lstrip("/"))

    absolute_local_path = work_dir / local_path
    if not absolute_local_path.exists():
      raise exceptions.BadFileException(
          f"File in YAML does not exist locally: {local_path}"
      )

    action["filename"] = f"{artifact_base_uri}{local_path.as_posix()}"

    env_pack_path = work_dir / ENV_PACK_FILE
    if env_pack_path.exists():
      env_pack_uri = f"{artifact_base_uri}{ENV_PACK_FILE}#libs"

      if "archives" not in action:
        action["archives"] = []

      if not any(env_pack_uri in arch for arch in action["archives"]):
        action["archives"].append(env_pack_uri)

    # Add PYTHONPATH to Spark driver and executors to include the site-packages
    # from the uploaded dependencies.zip, allowing the Spark jobs to find
    # the required Python libraries.
    full_python_path = "./libs/site-packages"
    props = _GetNestedDict(
        action, ["config", "sessionTemplate", "inline", "properties"]
    )
    props["spark.dataproc.driverEnv.PYTHONPATH"] = full_python_path
    props["spark.executorEnv.PYTHONPATH"] = full_python_path

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
