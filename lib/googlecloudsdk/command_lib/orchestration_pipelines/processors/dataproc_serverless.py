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
"""Dataproc Serverless action processor."""


from typing import Optional

from googlecloudsdk.command_lib.orchestration_pipelines.processors import base


class DataprocServerlessActionProcessor(base.ActionProcessor):
  """Action processor for Dataproc Serverless actions."""

  def _get_python_version(self) -> Optional[str]:
    # See
    # https://docs.cloud.google.com/dataproc-serverless/docs/concepts/versions/dataproc-serverless-versions
    engine_config = self.action.get("engine", {}).get("dataprocServerless", {})
    resource_profile = engine_config.get("resourceProfile", {})

    runtime_version = (
        resource_profile.get("inline", {})
        .get("runtimeConfig", {})
        .get("version")
    )
    if not runtime_version:
      return "3.12"
    return "3.11" if str(runtime_version).startswith("2.3") else "3.12"

  def _update_yaml_properties(self, action):
    if not self._env_pack_file:
      return

    # Add PYTHONPATH to Spark driver and executors
    # to include the site-packages
    # from the uploaded dependencies.zip, allowing the Spark jobs to find
    # the required Python libraries.
    props = self._get_nested_dict(
        action,
        [
            "engine",
            "dataprocServerless",
            "resourceProfile",
            "inline",
            "runtimeConfig",
            "properties",
        ],
    )
    props["spark.dataproc.driverEnv.PYTHONPATH"] = self.full_python_path
    props["spark.executorEnv.PYTHONPATH"] = self.full_python_path
