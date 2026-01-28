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
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml

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
      ignored_patterns = [".pyc", "__pycache__"]
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
    log.error("GCS Operation Failed: %s", e.stderr)
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
      log.error("Failed to upload string to %s: %s", dest, stderr.decode())
      raise exceptions.ToolException("String upload to GCS failed.")


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

  def Run(self, args):
    work_dir = pathlib.Path.cwd()

    _CheckGitStatus(self._subprocess)
    version_id = _GetVersionId(self._subprocess)
    composer_bucket = _GetComposerBucket(self._subprocess, COMPOSER_ENV_NAME)

    artifact_base_path = f"pipelines/{PIPELINE_ID}/versions/{version_id}/"
    artifact_base_uri = f"gs://{ARTIFACT_BUCKET_NAME}/{artifact_base_path}"

    template_path = work_dir / TEMPLATE_FILE
    if not template_path.exists():
      raise exceptions.BadFileException(f"File not found: {template_path}")

    resolved_pipeline = yaml.load_path(str(template_path))

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

    log.status.Print("Deployment Successful for version %s", version_id)
    return {"status": "SUCCESS", "version": version_id}

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
      env_pack_uri = f"{artifact_base_uri}{ENV_PACK_FILE}"

      if "archives" not in action:
        action["archives"] = []

      if not any(env_pack_uri in arch for arch in action["archives"]):
        action["archives"].append(env_pack_uri)

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
