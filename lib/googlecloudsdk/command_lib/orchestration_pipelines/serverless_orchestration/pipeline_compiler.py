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
"""Compiles a loaded pipeline and its uploaded artifacts into an API body."""

from collections.abc import Mapping, Sequence
import dataclasses
from typing import Any

from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import pipeline_loader
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.clients import gcs_client


@dataclasses.dataclass(frozen=True)
class CompiledPipeline:
  """The Orchestration API representation of a deployment."""

  parent: str
  pipeline_id: str
  body: Mapping[str, Any]
  version_id: str

  @property
  def name(self) -> str:
    """Full resource name of the pipeline."""
    return f"{self.parent}/pipelines/{self.pipeline_id}"


def Compile(
    loaded: pipeline_loader.LoadedPipeline,
    uploaded: Mapping[str, Sequence[gcs_client.UploadedArtifact]],
    version_id: str,
) -> CompiledPipeline:
  """Maps the loaded pipeline and its artifacts to an API pipeline body.

  Args:
    loaded: The loaded pipeline.
    uploaded: The uploaded artifacts of every action, keyed by action name.
    version_id: The artifact version being deployed.

  Returns:
    The compiled pipeline.
  """
  # TODO(b/567520802): Build the pipeline body (actions with gs:// URIs,
  # triggers, execution identity) per the Orchestration API proto.
  del loaded, uploaded, version_id
  raise errors.NotImplementedYetError("Compile is not implemented yet.")
