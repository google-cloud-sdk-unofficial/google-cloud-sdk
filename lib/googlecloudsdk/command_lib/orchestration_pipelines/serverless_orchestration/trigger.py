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
from collections.abc import Iterator, Mapping
import contextlib
import re
import time
from typing import Any

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.clients import orchestration_client
from googlecloudsdk.command_lib.orchestration_pipelines.tools import composer_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_RUNNER_LOCATION_PATH_RE = re.compile(
    r"projects/(?P<project>[^/\s]+)/locations/(?P<location>[^/\s]+)/?"
)
_TERMINAL_RUN_STATES = frozenset({"SUCCEEDED", "FAILED"})
# `GetPipelineRun` errors retried while polling, and how many in a row.
_TRANSIENT_POLL_ERROR_CODES = frozenset({"UNAVAILABLE", "DEADLINE_EXCEEDED"})
_MAX_CONSECUTIVE_POLL_FAILURES = 3


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


def GetPipelineResourceName(args: argparse.Namespace) -> str:
  """Builds the full pipeline resource name from `--runner` and `--pipeline`.

  Args:
    args: The parsed command-line arguments.

  Returns:
    The `projects/<project>/locations/<location>/pipelines/<id>` resource name.

  Raises:
    calliope_exceptions.RequiredArgumentException: If `--pipeline` is missing
      or blank.
    calliope_exceptions.InvalidArgumentException: If `--pipeline` is a path or
      `--runner` is not a valid Orchestration location resource name.
  """
  pipeline_id = _GetPipelineIdFromArgs(args)
  project, location = _GetProjectAndLocationFromRunnerArg(args)
  return f"projects/{project}/locations/{location}/pipelines/{pipeline_id}"


def Trigger(
    args: argparse.Namespace,
    *,
    api_client: orchestration_client.OrchestrationClient | None = None,
) -> dict[str, Any]:
  """Creates a pipeline run and waits for completion unless `--async` is set.

  Args:
    args: The parsed command-line arguments.
    api_client: Optional Orchestration API client (injected in tests).

  Returns:
    A status dict matching the Composer `trigger` output shape:
    `{"result": "success", "pipelineRuns": [...]}` or
    `{"result": "failed", "reason": ...}`.
  """
  pipeline_resource_name = GetPipelineResourceName(args)
  pipeline_id = _GetPipelineIdFromArgs(args)
  project, _ = _GetProjectAndLocationFromRunnerArg(args)
  with _UseProjectForApiCalls(project):
    api_client = api_client or orchestration_client.OrchestrationClient()
    log.status.Print(f"Triggering pipeline run for {pipeline_id}...")
    pipeline_run = api_client.CreatePipelineRun(
        pipeline_name=pipeline_resource_name,
        variables=args.substitutions,
    )
    if args.async_:
      log.status.Print(
          f"Pipeline run {_GetRunIdFromPipelineRun(pipeline_run)} was"
          " triggered. Exiting due to --async flag."
      )
      return _BuildTriggerResult(pipeline_run, args)
    return _WaitForPipelineRunCompletion(api_client, pipeline_run, args)


def _GetOrchestrationServicePrefix() -> str:
  """Returns the `//orchestration.<universe_domain>/` runner prefix."""
  return f"//orchestration.{properties.VALUES.core.universe_domain.Get()}/"


def _GetPipelineIdFromArgs(args: argparse.Namespace) -> str:
  """Returns the validated `--pipeline` ID from `args`."""
  pipeline_id = args.pipeline
  if not isinstance(pipeline_id, str) or not pipeline_id.strip():
    raise calliope_exceptions.RequiredArgumentException(
        "--pipeline", "The ID of the pipeline to trigger."
    )
  pipeline_id = pipeline_id.strip()
  if "/" in pipeline_id:
    raise calliope_exceptions.InvalidArgumentException(
        "--pipeline", "Pipeline must be a pipeline ID, not a resource path."
    )
  return pipeline_id


def _GetProjectAndLocationFromRunnerArg(
    args: argparse.Namespace,
) -> tuple[str, str]:
  """Returns `(project, location)` parsed from `--runner` in `args`."""
  runner_field = str(args.runner or "")
  expected_runner_prefix = _GetOrchestrationServicePrefix()
  location_path_match = _RUNNER_LOCATION_PATH_RE.fullmatch(
      runner_field.removeprefix(expected_runner_prefix)
  )
  if (
      not runner_field.startswith(expected_runner_prefix)
      or location_path_match is None
  ):
    raise calliope_exceptions.InvalidArgumentException(
        "--runner",
        "Runner must be a full Orchestration location resource name. "
        f'Example: "{expected_runner_prefix}'
        'projects/PROJECT_ID/locations/LOCATION"',
    )
  return location_path_match["project"], location_path_match["location"]


@contextlib.contextmanager
def _UseProjectForApiCalls(project: str) -> Iterator[None]:
  """Sends API calls and their quota usage to `project` inside the block."""
  original_project = properties.VALUES.core.project.Get()
  original_quota_project = properties.VALUES.billing.quota_project.Get()
  properties.VALUES.core.project.Set(project)
  properties.VALUES.billing.quota_project.Set(project)
  try:
    yield
  finally:
    properties.VALUES.core.project.Set(original_project)
    properties.VALUES.billing.quota_project.Set(original_quota_project)


def _WaitForPipelineRunCompletion(
    api_client: orchestration_client.OrchestrationClient,
    pipeline_run: Mapping[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
  """Waits for `pipeline_run` to finish and builds the command output."""
  log.status.Print(
      f"Pipeline run {_GetRunIdFromPipelineRun(pipeline_run)} was triggered."
      " Waiting for the pipeline run to complete..."
  )
  try:
    pipeline_run = _PollPipelineRunUntilTerminal(api_client, pipeline_run)
  except KeyboardInterrupt:
    return {
        "result": "success",
        "reason": (
            "The command was interrupted, but the process is still running"
            " in the background."
        ),
    }
  return _BuildTriggerResult(pipeline_run, args)


def _PollPipelineRunUntilTerminal(
    api_client: orchestration_client.OrchestrationClient,
    pipeline_run: Mapping[str, Any],
) -> Mapping[str, Any]:
  """Polls `GetPipelineRun` until `pipeline_run` reaches a terminal state."""
  pipeline_run_name = str(pipeline_run.get("name") or "").strip()
  if (
      _GetStateFromPipelineRun(pipeline_run) not in _TERMINAL_RUN_STATES
      and not pipeline_run_name
  ):
    raise errors.OrchestrationApiError(
        "PipelineRun is not in a terminal state and has no 'name' to poll."
    )
  start_time = time.time()
  consecutive_poll_failures = 0
  while _GetStateFromPipelineRun(pipeline_run) not in _TERMINAL_RUN_STATES:
    composer_utils.sleep_with_jitter()
    log.status.Print(f"Waiting... ({int(time.time() - start_time)}s elapsed)")
    try:
      pipeline_run = api_client.GetPipelineRun(pipeline_run_name)
      consecutive_poll_failures = 0
    except errors.OrchestrationApiError as e:
      consecutive_poll_failures += 1
      _VerifyPollErrorIsRetryable(e, consecutive_poll_failures)
      log.warning(
          "Retrying after a failed poll of %s: %s", pipeline_run_name, e
      )
  return pipeline_run


def _VerifyPollErrorIsRetryable(
    error: errors.OrchestrationApiError, consecutive_poll_failures: int
) -> None:
  """Re-raises `error` unless it is transient and the retry budget remains."""
  if (
      error.code not in _TRANSIENT_POLL_ERROR_CODES
      or consecutive_poll_failures >= _MAX_CONSECUTIVE_POLL_FAILURES
  ):
    raise error


def _BuildTriggerResult(
    pipeline_run: Mapping[str, Any], args: argparse.Namespace
) -> dict[str, Any]:
  """Builds the command output for `pipeline_run` in its current state."""
  if _GetStateFromPipelineRun(pipeline_run) == "FAILED":
    run_id = _GetRunIdFromPipelineRun(pipeline_run)
    return {
        "result": "failed",
        "reason": (
            f"Pipeline run {run_id} failed; inspect"
            f" {pipeline_run.get('name')} for the failure details."
        ),
    }
  return {
      "result": "success",
      "pipelineRuns": [_FormatPipelineRunOutput(pipeline_run, args)],
  }


def _GetRunIdFromPipelineRun(pipeline_run: Mapping[str, Any]) -> str:
  """Returns the run ID from the last segment of `pipeline_run['name']`."""
  return str(pipeline_run.get("name", "")).rsplit("/", 1)[-1]


def _GetStateFromPipelineRun(pipeline_run: Mapping[str, Any]) -> str:
  """Returns the `PipelineRun.state` name, or `STATE_UNSPECIFIED` when unset."""
  return str(pipeline_run.get("state") or "STATE_UNSPECIFIED")


def _FormatPipelineRunOutput(
    pipeline_run: Mapping[str, Any], args: argparse.Namespace
) -> dict[str, Any]:
  """Formats `pipeline_run` into the CLI output dictionary for `args`."""
  return {
      "pipeline_run_id": _GetRunIdFromPipelineRun(pipeline_run),
      "bundle_id": args.bundle,
      "pipeline_id": _GetPipelineIdFromArgs(args),
      "state": _GetStateFromPipelineRun(pipeline_run),
      "start_date": pipeline_run.get("startTime"),
      "end_date": pipeline_run.get("endTime"),
      "metadata": {
          "name": pipeline_run.get("name"),
      },
  }
