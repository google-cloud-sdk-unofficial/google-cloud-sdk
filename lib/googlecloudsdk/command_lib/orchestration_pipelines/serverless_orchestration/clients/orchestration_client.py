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
"""Client for the Serverless Orchestration API."""

from collections.abc import Mapping
from typing import Any

from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors


class OrchestrationClient:
  """Pipeline and pipeline-run operations used by the deploy and trigger flows.

  Resources and operations are exchanged as JSON-style mappings (the shape of
  `apitools` `encoding.MessageToPyValue`): camelCase field names, enum values
  as their string names (e.g. `"state": "SUCCEEDED"`), and timestamps as
  RFC 3339 strings. A `PipelineRun` carries `name`, `state`, `startTime`,
  `endTime` and, when failed, `error: {"message": ...}`.

  API failures surface as `calliope_exceptions.HttpException`, the gcloud
  convention for apitools errors, rather than a custom error type.
  """

  def GetPipeline(self, name: str) -> Mapping[str, Any] | None:
    """Returns the pipeline resource, or None if it does not exist."""
    # TODO(b/567520802): Implement.
    del name
    raise errors.NotImplementedYetError("GetPipeline is not implemented yet.")

  def CreatePipeline(
      self,
      parent: str,
      pipeline_id: str,
      body: Mapping[str, Any],
      request_id: str | None = None,
  ) -> Mapping[str, Any]:
    """Creates a pipeline and returns the long-running operation.

    Args:
      parent: `projects/<project>/locations/<location>`.
      pipeline_id: Id of the pipeline to create under `parent`.
      body: The `Pipeline` resource as a JSON-style mapping.
      request_id: Optional UUID4 that makes a retried request idempotent.
    """
    # TODO(b/567520802): Implement.
    del parent, pipeline_id, body, request_id
    raise errors.NotImplementedYetError(
        "CreatePipeline is not implemented yet."
    )

  def UpdatePipeline(
      self,
      name: str,
      body: Mapping[str, Any],
      update_mask: str | None = None,
      request_id: str | None = None,
  ) -> Mapping[str, Any]:
    """Updates a pipeline and returns the long-running operation.

    Args:
      name: `projects/<project>/locations/<location>/pipelines/<pipeline_id>`.
      body: The `Pipeline` resource as a JSON-style mapping.
      update_mask: Comma-separated field paths to overwrite. `None` replaces
        the whole resource; the deploy flow relies on this because the
        pipeline YAML is the source of truth, so fields removed from it must
        be cleared.
      request_id: Optional UUID4 that makes a retried request idempotent.
    """
    # TODO(b/567520802): Implement.
    del name, body, update_mask, request_id
    raise errors.NotImplementedYetError(
        "UpdatePipeline is not implemented yet."
    )

  def CreatePipelineRun(
      self,
      pipeline_name: str,
      run_id: str | None = None,
      variables: Mapping[str, str] | None = None,
  ) -> Mapping[str, Any]:
    """Starts a run of the pipeline and returns the long-running operation.

    The run is created under the location of `pipeline_name`. Wait for the
    returned operation (`WaitOperation`) and then poll `GetPipelineRun`.

    Args:
      pipeline_name: Full resource name of the pipeline to run.
      run_id: The `pipeline_run_id`. The API requires one, so a unique id is
        generated when omitted.
      variables: Runtime variables that override the pipeline defaults.

    Returns:
      The long-running operation whose response is the `PipelineRun`.
    """
    # TODO(b/567520802): Implement once the API exposes `PipelineRun.pipeline`
    # and `PipelineRun.variables`.
    del pipeline_name, run_id, variables
    raise errors.NotImplementedYetError(
        "CreatePipelineRun is not implemented yet."
    )

  def GetPipelineRun(self, run_name: str) -> Mapping[str, Any]:
    """Returns the current state of a pipeline run."""
    # TODO(b/567520802): Implement.
    del run_name
    raise errors.NotImplementedYetError(
        "GetPipelineRun is not implemented yet."
    )

  def WaitOperation(
      self, operation: Mapping[str, Any], timeout_seconds: int = 600
  ) -> Mapping[str, Any]:
    """Blocks until the operation completes and returns its response."""
    # TODO(b/567520802): Implement.
    del operation, timeout_seconds
    raise errors.NotImplementedYetError("WaitOperation is not implemented yet.")
