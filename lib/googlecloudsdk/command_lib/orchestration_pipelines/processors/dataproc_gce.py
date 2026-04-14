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
    dp_on_gce = self.action.get("engine", {}).get("dataprocOnGce", {})
    cluster_base = dp_on_gce.get("ephemeralCluster", {})
    config = cluster_base.get("resourceProfile", {}).get("inline", {})
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
    if not self._env_pack_file:
      return

    job_props = self._get_nested_dict(
        action,
        ["engine", "dataprocOnGce", "ephemeralCluster", "job", "properties"],
    )
    deploy_mode = job_props.get("spark.submit.deployMode", "client")
    job_props["spark.executorEnv.PYTHONPATH"] = self.full_python_path
    if deploy_mode == "cluster":
      job_props["spark.yarn.appMasterEnv.PYTHONPATH"] = self.full_python_path
    else:
      cluster_config = self._get_nested_dict(
          action,
          [
              "engine",
              "dataprocOnGce",
              "ephemeralCluster",
              "resourceProfile",
              "inline",
              "clusterConfig",
          ],
      )
      initialization_actions = cluster_config.setdefault(
          "initialization_actions", []
      )

      # Directory name where dependencies are unpacked.
      libs_dir = f"./{self.LIBS_EXTRACT_DIR}"
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
