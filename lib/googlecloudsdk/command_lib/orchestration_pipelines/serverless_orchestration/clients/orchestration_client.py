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

from collections.abc import Callable, Mapping
import datetime
import json
import re
import time
import types
from typing import Any
import uuid

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import extra_types
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.core import ecp_proxy_manager

API_NAME = "orchestration"
API_VERSION = "v1beta"
_DEFAULT_POLL_INTERVAL_SECONDS = 5

_HTTP_STATUS_TO_RPC_CODE = types.MappingProxyType({
    400: "INVALID_ARGUMENT",
    401: "UNAUTHENTICATED",
    403: "PERMISSION_DENIED",
    404: "NOT_FOUND",
    409: "ALREADY_EXISTS",
    412: "FAILED_PRECONDITION",
    429: "RESOURCE_EXHAUSTED",
    499: "CANCELLED",
    500: "INTERNAL",
    501: "UNIMPLEMENTED",
    503: "UNAVAILABLE",
    504: "DEADLINE_EXCEEDED",
})

_RPC_CODE_TO_NAME = types.MappingProxyType({
    0: "OK",
    1: "CANCELLED",
    2: "UNKNOWN",
    3: "INVALID_ARGUMENT",
    4: "DEADLINE_EXCEEDED",
    5: "NOT_FOUND",
    6: "ALREADY_EXISTS",
    7: "PERMISSION_DENIED",
    8: "RESOURCE_EXHAUSTED",
    9: "FAILED_PRECONDITION",
    10: "ABORTED",
    11: "OUT_OF_RANGE",
    12: "UNIMPLEMENTED",
    13: "INTERNAL",
    14: "UNAVAILABLE",
    15: "DATA_LOSS",
    16: "UNAUTHENTICATED",
})


class OrchestrationClient:
  """Client for Serverless Orchestration pipelines and pipeline runs."""

  def __init__(
      self,
      poll_interval_seconds: float = _DEFAULT_POLL_INTERVAL_SECONDS,
      client: Any = None,
  ):
    """Initializes the instance.

    Args:
      poll_interval_seconds: Seconds to wait between `GetOperation` polls.
      client: Optional `orchestration` `v1beta` apitools client; created lazily
        if None, honoring the `api_endpoint_overrides/orchestration` property.
    """
    self._poll_interval_seconds = poll_interval_seconds
    self._client = client
    self._messages = apis.GetMessagesModule(API_NAME, API_VERSION)

  def GetPipeline(self, name: str) -> Mapping[str, Any] | None:
    """Returns the pipeline resource for `name`, or None if not found."""
    request = self._messages.OrchestrationProjectsLocationsPipelinesGetRequest(
        name=name
    )
    try:
      return _CallApi(
          self._GetApiClient().projects_locations_pipelines.Get, request
      )
    except errors.OrchestrationApiError as e:
      if e.code == "NOT_FOUND":
        return None
      raise

  def CreatePipeline(
      self,
      parent: str,
      pipeline_id: str,
      body: Mapping[str, Any],
      request_id: str | None = None,
  ) -> Mapping[str, Any]:
    """Creates a pipeline and returns the long-running operation.

    Args:
      parent: Parent location resource name (`projects/<p>/locations/<l>`).
      pipeline_id: Pipeline identifier to create under `parent`.
      body: `Pipeline` resource fields keyed by their JSON names (`spec`,
        `executionIdentity`, etc.).
      request_id: Optional idempotency UUID; omitted from the request if None.

    Returns:
      The `google.longrunning.Operation` mapping returned by the API.
    """
    name = f"{parent}/pipelines/{pipeline_id}"
    messages = self._messages
    request = messages.OrchestrationProjectsLocationsPipelinesCreateRequest(
        parent=parent,
        pipelineId=pipeline_id,
        pipeline=self._BuildPipeline(name, body),
        requestId=request_id,
    )
    return _CallApi(
        self._GetApiClient().projects_locations_pipelines.Create, request
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
      name: Full pipeline resource name (`projects/<p>/locations/<l>/...`).
      body: `Pipeline` resource fields to update, keyed by their JSON names.
      update_mask: Comma-separated field mask; replaces the full definition if
        None.
      request_id: Optional idempotency UUID; omitted from the request if None.

    Returns:
      The `google.longrunning.Operation` mapping returned by the API.
    """
    messages = self._messages
    request = messages.OrchestrationProjectsLocationsPipelinesPatchRequest(
        name=name,
        pipeline=self._BuildPipeline(name, body),
        updateMask=update_mask,
        requestId=request_id,
    )
    return _CallApi(
        self._GetApiClient().projects_locations_pipelines.Patch, request
    )

  def CreatePipelineRun(
      self,
      pipeline_name: str,
      run_id: str | None = None,
      variables: Mapping[str, str] | None = None,
      request_id: str | None = None,
  ) -> Mapping[str, Any]:
    """Starts a batch run of `pipeline_name` and returns the `PipelineRun`.

    Args:
      pipeline_name: Full pipeline resource name.
      run_id: Run identifier; auto-generated if None.
      variables: Optional runtime parameter key/value pairs; omitted if None.
      request_id: Optional idempotency UUID; omitted from the request if None.

    Returns:
      The created `PipelineRun` resource mapping.
    """
    _, pipeline_id = _SplitPipelineName(pipeline_name)
    resolved_run_id = run_id or _GenerateRunId(pipeline_id)
    messages = self._messages
    pipeline_run = messages.PipelineRun(
        name=f"{pipeline_name}/runs/{resolved_run_id}",
        runMode=messages.PipelineRun.RunModeValueValuesEnum.BATCH,
    )
    if variables:
      pipeline_run.parameters = _BuildRunParameters(
          messages.PipelineRun.ParametersValue, variables
      )
    request = messages.OrchestrationProjectsLocationsPipelinesRunsCreateRequest(
        parent=pipeline_name,
        pipelineRun=pipeline_run,
        pipelineRunId=resolved_run_id,
        requestId=request_id,
    )
    return _CallApi(
        self._GetApiClient().projects_locations_pipelines_runs.Create, request
    )

  def GetPipelineRun(self, run_name: str) -> Mapping[str, Any]:
    """Returns the current state of a pipeline run."""
    messages = self._messages
    request = messages.OrchestrationProjectsLocationsPipelinesRunsGetRequest(
        name=run_name
    )
    return _CallApi(
        self._GetApiClient().projects_locations_pipelines_runs.Get, request
    )

  def GetOperation(self, name: str) -> Mapping[str, Any]:
    """Returns the long-running operation."""
    request = self._messages.OrchestrationProjectsLocationsOperationsGetRequest(
        name=name
    )
    return _CallApi(
        self._GetApiClient().projects_locations_operations.Get, request
    )

  def WaitOperation(
      self, operation: Mapping[str, Any], timeout_seconds: int = 600
  ) -> Mapping[str, Any]:
    """Polls until `operation` completes and returns the resulting resource."""
    name = str(operation.get("name") or "").strip()
    if not operation.get("done") and not name:
      raise errors.OrchestrationApiError(
          "Operation is not done and has no 'name' to poll."
      )
    deadline = time.monotonic() + timeout_seconds
    while not operation.get("done"):
      if time.monotonic() >= deadline:
        raise errors.OrchestrationApiError(
            f"Operation {name} did not complete within {timeout_seconds}s.",
            code="DEADLINE_EXCEEDED",
        )
      time.sleep(self._poll_interval_seconds)
      operation = self.GetOperation(name)
    error = operation.get("error")
    if error:
      error_message = _FormatOperationError(error)
      code = (
          _FormatRpcCode(error.get("code"))
          if isinstance(error, Mapping)
          else None
      )
      raise errors.OrchestrationApiError(
          f"Operation {name} failed: {error_message}",
          code=code,
      )
    return operation.get("response") or {}

  def _GetApiClient(self) -> Any:
    """Returns the apitools client, creating it on first use."""
    if self._client is None:
      try:
        self._client = apis.GetClientInstance(API_NAME, API_VERSION)
      # With certificate-based access, creating the client fails if the client
      # certificate cannot be loaded (`OSError`) or the local ECP proxy is not
      # running (`ECPProxyError`).
      except (OSError, ecp_proxy_manager.ECPProxyError) as e:
        raise errors.OrchestrationApiError(
            f"Failed to create the Orchestration API client: {e}"
        ) from e
    return self._client

  def _BuildPipeline(self, name: str, body: Mapping[str, Any]) -> Any:
    """Returns the `Pipeline` message for the JSON-style `body` fields.

    Args:
      name: Full pipeline resource name.
      body: `Pipeline` resource fields keyed by their JSON names.

    Raises:
      messages_util.DecodeError: If `body` has a field that `Pipeline` does not
        define, such as a `snake_case` name, which `encoding.DictToMessage`
        would silently keep as an unrecognized field.
    """
    return messages_util.DictToMessageWithErrorCheck(
        {**body, "name": name}, self._messages.Pipeline
    )


def _CallApi(method: Callable[[Any], Any], request: Any) -> dict[str, Any]:
  """Calls apitools `method` with `request` and returns the JSON response.

  Args:
    method: Bound apitools service method, for example
      `client.projects_locations_pipelines.Get`.
    request: The request message for `method`.

  Returns:
    The response message as a JSON-style dict with REST field names.

  Raises:
    errors.OrchestrationApiError: If the request fails.
  """
  method_id = method.method_config().method_id
  try:
    response = method(request)
  except apitools_exceptions.HttpError as e:
    raise _HttpErrorToApiError(method_id, e) from e
  # Clients from `apis.GetClientInstance` wrap the `HttpError` in an
  # `HttpException` if the API is disabled and the prompt to enable it is
  # declined or suppressed (for example, with `--quiet`).
  except api_exceptions.HttpException as e:
    raise _HttpErrorToApiError(method_id, e.error) from e
  # With certificate-based access, the local ECP proxy adapter wraps transport
  # and proxy failures in `ECPProxyError`, which is not an `OSError`.
  except (
      apitools_exceptions.CommunicationError,
      OSError,
      ecp_proxy_manager.ECPProxyError,
  ) as e:
    raise errors.OrchestrationApiError(f"{method_id} failed: {e}") from e
  return encoding.MessageToDict(response)


def _HttpErrorToApiError(
    method_id: str, http_error: apitools_exceptions.HttpError
) -> errors.OrchestrationApiError:
  """Returns the `OrchestrationApiError` for an HTTP error of `method_id`."""
  message, code = _ExtractHttpError(
      http_error.status_code,
      http_error.response.get("reason"),
      _DecodeContent(http_error.content),
  )
  return errors.OrchestrationApiError(
      f"{method_id} failed: {message}", code=code
  )


def _BuildRunParameters(
    parameters_type: Any, variables: Mapping[str, str]
) -> Any:
  """Returns `variables` as a `PipelineRun.parameters` map of string values."""
  return parameters_type(
      additionalProperties=[
          parameters_type.AdditionalProperty(
              key=str(key), value=extra_types.JsonValue(string_value=str(value))
          )
          for key, value in sorted(variables.items())
      ]
  )


def _SplitPipelineName(pipeline_name: str) -> tuple[str, str]:
  """Splits a pipeline resource name into `(parent, pipeline_id)`."""
  parent, _, pipeline_id = pipeline_name.partition("/pipelines/")
  if not parent or not pipeline_id or "/" in pipeline_id:
    raise errors.OrchestrationApiError(
        f"Invalid pipeline resource name: '{pipeline_name}'."
    )
  return parent, pipeline_id


def _GenerateRunId(pipeline_id: str) -> str:
  """Generates a unique, resource-id-safe `pipeline_run_id`."""
  safe_id = re.sub(r"[^a-z0-9-]+", "-", pipeline_id.lower()).strip("-") or "run"
  if not safe_id[0].isalpha():
    safe_id = f"r-{safe_id}"
  timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
      "%Y%m%d%H%M%S"
  )
  return f"{safe_id[:32].rstrip('-')}-{timestamp}-{uuid.uuid4().hex[:8]}"


def _FormatRpcCode(code: Any) -> str | None:
  """Maps a `google.rpc.Code` value to its canonical string name."""
  if code is None:
    return None
  if isinstance(code, int) and not isinstance(code, bool):
    return _RPC_CODE_TO_NAME.get(code, str(code))
  return str(code)


def _DecodeContent(content: bytes | str | None) -> str:
  """Returns the text of an HTTP error response body."""
  if isinstance(content, bytes):
    return content.decode("utf-8", errors="replace")
  return content or ""


def _ExtractHttpError(
    status_code: int, reason: str | None, body_text: str
) -> tuple[str, str]:
  """Extracts `(message, canonical_code)` from an HTTP error response."""
  fallback_code = _HTTP_STATUS_TO_RPC_CODE.get(status_code, str(status_code))
  stripped = body_text.strip()
  if stripped:
    try:
      parsed = json.loads(stripped)
    except ValueError:
      parsed = None
    if isinstance(parsed, Mapping):
      error_obj = parsed.get("error")
      if isinstance(error_obj, Mapping):
        message = _FormatOperationError(error_obj)
        status = error_obj.get("status")
        if isinstance(status, str) and status.strip():
          return message, status.strip()
        return message, fallback_code
  summary = stripped or (reason or f"HTTP {status_code}")
  return summary, fallback_code


def _FormatOperationError(error: Any) -> str:
  """Formats an API or LRO `error` mapping, including any `DebugInfo.detail`."""
  if not isinstance(error, Mapping):
    return str(error)
  message = str(error.get("message") or error)
  seen = {message}
  extra_details: list[str] = []
  details = error.get("details")
  if isinstance(details, list):
    for item in details:
      if not isinstance(item, Mapping):
        continue
      detail = item.get("detail")
      detail_text = detail.strip() if isinstance(detail, str) else None
      if detail_text and detail_text not in seen:
        seen.add(detail_text)
        extra_details.append(detail_text)
  if extra_details:
    return f"{message} ({'; '.join(extra_details)})"
  return message
