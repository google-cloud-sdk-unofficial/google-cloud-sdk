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
"""Utilities for interacting with GCS."""

import json
import subprocess
import time
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml

ORCHESTRATION_PIPELINES_DATA_DIRECTORY = "data"
ORCHESTRATION_PIPELINES_DAGS_DIRECTORY = "dags/orchestration_pipelines"
MANIFEST_FILE_NAME = "manifest.yml"
MAX_RETRIES = 5


def UploadFile(
    subprocess_mod, content, dest, file_name, if_generation_match=None
):
  """Uploads files to GCS, optionally with optimistic locking.

  Args:
    subprocess_mod: The subprocess module to use.
    content: The content to upload.
    dest: The GCS destination path.
    file_name: The name of the file being uploaded (for error messages).
    if_generation_match: If provided, GCS generation ID for optimistic locking.
  """
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
      raise core_exceptions.Error(
          f"Failed to upload {file_name} to {dest}: {stderr}"
      )


def FetchManifest(subprocess_mod, manifest_gcs_path):
  """Fetches manifest content and its GCS generation ID from a specific path.

  Args:
    subprocess_mod: The subprocess module to use.
    manifest_gcs_path: GCS path to the manifest file.

  Returns:
    A tuple containing:
      - dict: The manifest content parsed from YAML, or None if the manifest
        could not be fetched.
      - int: The GCS generation ID of the manifest file, or 0 if the manifest
        could not be fetched.
  """
  # 1. Get Generation ID (Metadata)
  try:
    meta_out = subprocess_mod.check_output(
        [
            "gcloud",
            "storage",
            "objects",
            "describe",
            manifest_gcs_path,
            "--format=json",
        ],
        text=True,
        stderr=subprocess_mod.DEVNULL,
    ).strip()
    metadata = json.loads(meta_out)
    generation = metadata.get("generation")
  except subprocess.CalledProcessError:
    return None, 0
  # 2. Get Content
  try:
    content_out = subprocess_mod.check_output(
        ["gcloud", "storage", "cp", manifest_gcs_path, "-"],
        text=True,
        stderr=subprocess_mod.DEVNULL,
    ).strip()
    return yaml.load(content_out), generation
  except subprocess.CalledProcessError:
    return None, 0


def UpdatePausedPipelinesInManifestWithRetry(
    subprocess_mod, manifest_gcs_path, pipeline, action, max_retries=MAX_RETRIES
):
  """Updates paused pipelines in the manifest file in GCS.

  Uses retry logic and optimistic locking to ensure successful update.

  Args:
    subprocess_mod: The subprocess module to use.
    manifest_gcs_path: GCS path to the manifest file.
    pipeline: The pipeline to add or remove from pausedPipelines.
    action: 'add' or 'remove' to indicate the action on pausedPipelines.
    max_retries: The maximum number of retries for updating the manifest.

  Returns:
    True if manifest was updated successfully or no update was needed,
    False otherwise.
  """
  attempts = 0
  while attempts < max_retries:
    manifest_data, read_generation_id = FetchManifest(
        subprocess_mod, manifest_gcs_path
    )
    if manifest_data is None:
      raise calliope_exceptions.BadFileException(
          f"Manifest file {manifest_gcs_path} not found."
      )

    paused_pipelines = manifest_data.get("pausedPipelines", [])

    if action == "add":
      if pipeline not in paused_pipelines:
        paused_pipelines.append(pipeline)
      else:
        # Pipeline is already in pausedPipelines list, no update needed.
        return True
    elif action == "remove":
      if pipeline in paused_pipelines:
        paused_pipelines.remove(pipeline)
      else:
        # Pipeline is not in pausedPipelines list, no update needed.
        return True
    else:
      raise ValueError("action must be 'add' or 'remove'")

    manifest_data["pausedPipelines"] = paused_pipelines
    try:
      log.status.Print(
          "Attempting to update manifest (Generation match:"
          f" {read_generation_id})..."
      )
      UploadFile(
          subprocess_mod,
          yaml.dump(manifest_data),
          manifest_gcs_path,
          MANIFEST_FILE_NAME,
          if_generation_match=read_generation_id,
      )
      return True
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
    raise calliope_exceptions.HttpException(
        "Failed to update manifest file due to race condition after maximum"
        " number of retries."
    )
  return True


def TouchPipelineFile(subprocess_mod, pipeline_gcs_path):
  """Touches the pipeline file to trigger the Airflow scheduler."""

  try:
    subprocess_mod.check_output(
        [
            "gcloud",
            "storage",
            "objects",
            "update",
            pipeline_gcs_path,
            f"--custom-metadata=modified_at={int(time.time())}",
        ],
        text=True,
        stderr=subprocess_mod.PIPE,
    )
  except subprocess.CalledProcessError as e:
    if "404" in e.stderr or "NotFound" in e.stderr:
      raise calliope_exceptions.BadFileException(
          f"Pipeline file not found: {pipeline_gcs_path}"
      )
    raise calliope_exceptions.HttpException(
        f"Failed to touch pipeline file {pipeline_gcs_path}: {e.stderr}"
    )
