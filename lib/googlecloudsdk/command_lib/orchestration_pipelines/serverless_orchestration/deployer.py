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
"""Deployer for Serverless Orchestration API pipelines."""

import argparse
import dataclasses
from typing import Any

from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors


@dataclasses.dataclass(frozen=True)
class DeployResult:
  """Outcome of a Serverless Orchestration deployment."""

  pipeline_name: str
  version_id: str
  artifacts: tuple[str, ...]
  operation: str | None
  status: str


def IsServerlessOrchestrationDeployment(args: argparse.Namespace) -> bool:
  """Returns True if the deployment targets the Serverless Orchestration API.

  Args:
    args: The parsed command-line arguments.
  """
  # TODO(b/567520802): Return True when the pipeline YAML selected by
  # `deployment.yaml` (or `./pipeline.yaml`) declares
  # `runner: orchestration_service`. Returns False until then so every
  # deployment keeps taking the Cloud Composer flow.
  del args
  return False


def Deploy(args: argparse.Namespace) -> dict[str, Any]:
  """Packages pipeline artifacts and deploys to the Orchestration service.

  Args:
    args: The parsed command-line arguments.

  Returns:
    The deployment result as a dict (see `DeployResult`).

  Raises:
    errors.NotImplementedYetError: Until the Serverless Orchestration
      deployment flow is implemented.
  """
  # TODO(b/567520802): pipeline_loader.LoadPipeline -> packagers.dbt.DbtPackager
  # -> clients.gcs_client.GcsClient -> pipeline_compiler.Compile ->
  # clients.orchestration_client.OrchestrationClient Create/UpdatePipeline ->
  # DeployResult.
  del args
  raise errors.NotImplementedYetError(
      "Serverless Orchestration deployment is not yet implemented."
  )
