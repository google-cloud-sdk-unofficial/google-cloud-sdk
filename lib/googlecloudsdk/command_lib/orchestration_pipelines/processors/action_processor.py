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
"""Action processors factory for Orchestration Pipelines."""

from googlecloudsdk.command_lib.orchestration_pipelines.processors import base
from googlecloudsdk.command_lib.orchestration_pipelines.processors import dataproc_gce
from googlecloudsdk.command_lib.orchestration_pipelines.processors import dataproc_serverless


def get_action_processor(
    action,
    work_dir,
    artifact_base_uri,
    subprocess_mod,
    defaults,
    requirements_path=None,
) -> base.ActionProcessor:
  """Returns the appropriate ActionProcessor for the given action."""
  engine = action.get("engine", {})
  engine_type = list(engine.keys())[0] if engine else None

  if engine_type == "dataprocServerless":
    return dataproc_serverless.DataprocServerlessActionProcessor(
        action,
        work_dir,
        artifact_base_uri,
        subprocess_mod,
        defaults,
        requirements_path,
    )
  if engine_type == "dataprocOnGce":
    return dataproc_gce.DataprocGCEActionProcessor(
        action,
        work_dir,
        artifact_base_uri,
        subprocess_mod,
        defaults,
        requirements_path,
    )
