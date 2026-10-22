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
"""Trigger flow for Serverless Orchestration API pipelines."""

import argparse
from typing import Any

from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.core import properties


def IsServerlessOrchestrationTrigger(runner: str | None) -> bool:
  """Returns True if `runner` targets the Serverless Orchestration API.

  Args:
    runner: The `--runner` flag value, or None when `--runner` is omitted.

  Returns:
    True when `runner` starts with `//orchestration.<universe_domain>/`, or
    False when `runner` is omitted or targets another service so the Cloud
    Composer flow handles the command.
  """
  return bool(runner and runner.startswith(_GetOrchestrationServicePrefix()))


def Trigger(args: argparse.Namespace) -> dict[str, Any]:
  """Creates a pipeline run and waits for completion unless `--async` is set.

  Args:
    args: The parsed command-line arguments.

  Returns:
    The command output in the shape of the Composer `trigger` flow.

  Raises:
    errors.NotImplementedYetError: Until the trigger flow is implemented.
  """
  # TODO(b/567520802): Resolve the pipeline name, call
  # clients.orchestration_client.OrchestrationClient().CreatePipelineRun, and
  # poll GetPipelineRun.
  del args
  raise errors.NotImplementedYetError("Trigger is not implemented yet.")


def _GetOrchestrationServicePrefix() -> str:
  """Returns the `//orchestration.<universe_domain>/` runner prefix."""
  return f"//orchestration.{properties.VALUES.core.universe_domain.Get()}/"
