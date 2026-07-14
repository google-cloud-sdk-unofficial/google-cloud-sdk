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
from googlecloudsdk.command_lib.orchestration_pipelines.tools import resource_profile_loader


class DataprocGCEActionProcessor(base.ActionProcessor):
  """Action processor for Dataproc GCE actions."""

  _EPHEMERAL_CLUSTER = "ephemeralCluster"
  _EXISTING_CLUSTER = "existingCluster"
  _DEPLOY_MODE_CLIENT = "client"
  _DEPLOY_MODE_CLUSTER = "cluster"

  def _get_python_version(self) -> Optional[str]:
    # See
    # https://docs.cloud.google.com/dataproc/docs/concepts/versioning/dataproc-version-clusters
    dp_on_gce = self.action.get("engine", {}).get("dataprocOnGce", {})
    ephemeral_cluster_config = dp_on_gce.get(self._EPHEMERAL_CLUSTER, {})
    if not ephemeral_cluster_config:
      # If there is no ephemeralCluster (e.g. existingCluster), we just
      # return None so it defaults to 3.11 below.
      if self.existing_cluster_image_version:
        image_version = self.existing_cluster_image_version
      else:
        image_version = None
    else:
      resource_profile = ephemeral_cluster_config.get("resourceProfile", {})
      config = resource_profile.get("inline")
      if config is None:
        external_profile = (
            resource_profile_loader.load_external_resource_profile(
                resource_profile, self._work_dir
            )
        )
        config = {}
        if external_profile:
          config = external_profile.get("definition", {}).get("config", {})

      image_version = config.get("softwareConfig", {}).get(
          "imageVersion"
      ) or config.get("config", {}).get("softwareConfig", {}).get(
          "imageVersion"
      )

    if image_version is None or str(image_version) == "None":
      resolved_version = "3.11"
    elif str(image_version).startswith("2.1"):
      resolved_version = "3.10"
    elif str(image_version).startswith("2.2"):
      resolved_version = "3.11"
    else:
      resolved_version = "3.12"

    return resolved_version

  def _update_yaml_properties(self, action):
    if not self._env_pack_file:
      return

    dp_on_gce = self.action.get("engine", {}).get("dataprocOnGce", {})
    if self._EPHEMERAL_CLUSTER in dp_on_gce:
      cluster_type = self._EPHEMERAL_CLUSTER
    elif self._EXISTING_CLUSTER in dp_on_gce:
      cluster_type = self._EXISTING_CLUSTER
    else:
      return

    job_props = self._get_nested_dict(
        action,
        ["engine", "dataprocOnGce", cluster_type, "properties"],
    )
    deploy_mode = job_props.get(
        "spark.submit.deployMode", self._DEPLOY_MODE_CLIENT
    )
    job_props["spark.executorEnv.PYTHONPATH"] = self.full_python_path

    if deploy_mode == self._DEPLOY_MODE_CLUSTER:
      job_props["spark.yarn.appMasterEnv.PYTHONPATH"] = self.full_python_path

    if (
        cluster_type == self._EPHEMERAL_CLUSTER
        and deploy_mode == self._DEPLOY_MODE_CLIENT
    ):
      # Directory name where dependencies are unpacked.
      libs_dir = f"./{self.LIBS_EXTRACT_DIR}"
      env_name = "python_environment"

      python_version = self._get_python_version()
      driver_python_path = (
          f"/opt/{env_name}/lib/python{python_version}/site-packages"
      )
      resource_profile = self._get_nested_dict(
          action,
          [
              "engine",
              "dataprocOnGce",
              self._EPHEMERAL_CLUSTER,
              "resourceProfile",
          ],
      )

      # Use 'overrides' if 'path' or 'externalConfigPath' is present,
      # otherwise default to 'inline'.
      if "path" in resource_profile or "externalConfigPath" in resource_profile:
        cluster_config = self._get_nested_dict(
            action,
            [
                "engine",
                "dataprocOnGce",
                self._EPHEMERAL_CLUSTER,
                "resourceProfile",
                "overrides",
                "config",
            ],
        )
      else:
        cluster_config = self._get_nested_dict(
            action,
            [
                "engine",
                "dataprocOnGce",
                self._EPHEMERAL_CLUSTER,
                "resourceProfile",
                "inline",
                "config",
            ],
        )

      initialization_actions = cluster_config.setdefault(
          "initialization_actions", []
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
    else:
      if deploy_mode == self._DEPLOY_MODE_CLIENT:
        job_props["dataproc:driver.unpack.archive.enable"] = "true"
        job_props["spark.dataproc.driverEnv.PYTHONPATH"] = self.full_python_path
