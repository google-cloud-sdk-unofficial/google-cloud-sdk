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
"""Dataproc GCE action processor."""


from typing import Optional

from googlecloudsdk.command_lib.orchestration_pipelines.processors import base
from googlecloudsdk.command_lib.orchestration_pipelines.tools import python_environment_unpack_renderer


class DataprocGCEActionProcessor(base.ActionProcessor):
  """Action processor for Dataproc GCE actions."""

  def _get_python_version(self) -> Optional[str]:
    # See
    # https://docs.cloud.google.com/dataproc/docs/concepts/versioning/dataproc-version-clusters
    config = self.action.get("config", {})
    image_version = str(
        config.get("softwareConfig", {}).get("imageVersion")
        or config.get("clusterConfig", {})
        .get("softwareConfig", {})
        .get("imageVersion")
    )
    if str(image_version) == "None":
      return "3.11"
    if image_version.startswith("2.1"):
      return "3.10"
    if image_version.startswith("2.2"):
      return "3.11"
    return "3.12"

  def _update_yaml_properties(self, action):
    # Add PYTHONPATH to Spark driver and executors to include the site-packages
    # from the uploaded dependencies.zip, allowing the Spark jobs to find
    # the required Python libraries.
    env_pack_path = self._work_dir / self._env_pack_file
    if not env_pack_path.exists():
      return

    extract_path = "libs"
    env_pack_uri = (
        f"{self._artifact_base_uri}{self._env_pack_file}#{extract_path}"
    )
    self.action.setdefault("archives", [])
    if not any(env_pack_uri in arch for arch in self.action["archives"]):
      self.action["archives"].append(env_pack_uri)

    job_props = self._get_nested_dict(action, ["config", "job", "properties"])
    deploy_mode = job_props.get("spark.submit.deployMode", "client")
    job_props["spark.executorEnv.PYTHONPATH"] = self.full_python_path
    if deploy_mode == "cluster":
      job_props["spark.yarn.appMasterEnv.PYTHONPATH"] = self.full_python_path
    else:
      cluster_config = self._get_nested_dict(
          action, ["config", "cluster_config"]
      )
      initialization_actions = cluster_config.setdefault(
          "initialization_actions", []
      )

      # Directory name where dependencies are unpacked.
      libs_dir = f"./{extract_path}"
      env_name = "python_environment"

      python_version = self._get_python_version()
      driver_python_path = (
          f"/opt/{env_name}/lib/python{python_version}/site-packages"
      )
      job_props["spark.dataproc.driverEnv.PYTHONPATH"] = driver_python_path
      gcs_archive_path = f"{self._artifact_base_uri}{self._env_pack_file}"

      python_environment_unpack_renderer.render_init_action(
          self._work_dir, libs_dir, env_name, gcs_archive_path
      )

      initialization_actions.append({
          "executable_file": (
              f"{self._artifact_base_uri}python_environment_unpack.sh"
          )
      })
