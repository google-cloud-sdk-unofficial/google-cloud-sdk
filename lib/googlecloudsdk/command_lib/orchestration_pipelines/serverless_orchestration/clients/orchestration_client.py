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
import datetime
import http
import json
import os
import re
import time
import types
from typing import Any
from urllib import parse as urllib_parse
import uuid

from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import requests as creds_requests
from googlecloudsdk.core.util import encoding

# gcloud-disable-gdu-domain
DEFAULT_ENDPOINT = "https://staging-orchestration.sandbox.googleapis.com"
ENDPOINT_ENV_VAR = "ORCHESTRATION_ENDPOINT"
API_VERSION = "v1alpha"
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
      session: Any = None,
  ):
    """Initializes the instance.

    Args:
      poll_interval_seconds: Seconds to wait between `GetOperation` polls.
      session: Optional authenticated HTTP `requests.Session`; created lazily
        via `creds_requests.GetSession()` if None.
    """
    custom_endpoint = encoding.GetEncodedValue(os.environ, ENDPOINT_ENV_VAR)
    self._base_url = _NormalizeBaseUrl(custom_endpoint or DEFAULT_ENDPOINT)
    self._poll_interval_seconds = poll_interval_seconds
    self._session = session

  def GetPipeline(self, name: str) -> Mapping[str, Any] | None:
    """Returns the pipeline resource for `name`, or None if not found."""
    try:
      return self._Request("GET", name)
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
      body: Pipeline resource fields (`versionId`, `spec`, etc.).
      request_id: Optional idempotency UUID; omitted from the request if None.

    Returns:
      The `google.longrunning.Operation` mapping returned by the API.
    """
    name = f"{parent}/pipelines/{pipeline_id}"
    params = {"pipelineId": pipeline_id}
    if request_id:
      params["requestId"] = request_id
    payload = {**body, "name": name}
    return self._Request(
        "POST", f"{parent}/pipelines", params=params, body=payload
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
      body: Pipeline resource fields to update.
      update_mask: Comma-separated field mask; replaces the full definition if
        None.
      request_id: Optional idempotency UUID; omitted from the request if None.

    Returns:
      The `google.longrunning.Operation` mapping returned by the API.
    """
    params: dict[str, str] = {}
    if update_mask:
      params["updateMask"] = update_mask
    if request_id:
      params["requestId"] = request_id
    payload = {**body, "name": name}
    return self._Request("PATCH", name, params=params or None, body=payload)

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
    run_name = f"{pipeline_name}/runs/{resolved_run_id}"
    pipeline_run: dict[str, Any] = {
        "name": run_name,
        "runMode": "BATCH",
    }
    if variables:
      pipeline_run["parameters"] = {
          str(key): str(value) for key, value in sorted(variables.items())
      }
    params = {"pipelineRunId": resolved_run_id}
    if request_id:
      params["requestId"] = request_id
    return self._Request(
        "POST",
        f"{pipeline_name}/runs",
        params=params,
        body=pipeline_run,
    )

  def GetPipelineRun(self, run_name: str) -> Mapping[str, Any]:
    """Returns the current state of a pipeline run."""
    return self._Request("GET", run_name)

  def GetOperation(self, name: str) -> Mapping[str, Any]:
    """Returns the long-running operation."""
    return self._Request("GET", name)

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

  @property
  def _http_session(self) -> Any:
    if self._session is None:
      self._session = creds_requests.GetSession()
    return self._session

  def _Request(
      self,
      method: str,
      path: str,
      *,
      params: Mapping[str, str] | None = None,
      body: Mapping[str, Any] | None = None,
  ) -> dict[str, Any]:
    """Sends an authenticated HTTP REST request and returns the parsed JSON."""
    url = _BuildRequestUrl(self._base_url, path, params)
    headers, data = _BuildRequestPayload(body)
    body_text = self._SendHttpRequest(method, url, headers=headers, data=data)
    return _ParseJsonResponse(method, url, body_text)

  def _SendHttpRequest(
      self,
      method: str,
      url: str,
      *,
      headers: Mapping[str, str],
      data: str | None,
  ) -> str:
    """Sends an HTTP request and returns the decoded response body text."""
    log.info("Calling %s %s", method, url)
    try:
      response = self._http_session.request(
          method, url, data=data, headers=headers
      )
    except OSError as e:
      raise errors.OrchestrationApiError(f"{method} {url} failed: {e}") from e

    status_code = int(response.status_code)
    body_text = _DecodeResponseText(response)
    if (
        status_code < http.HTTPStatus.OK
        or status_code >= http.HTTPStatus.MULTIPLE_CHOICES
    ):
      message, code = _ExtractHttpError(status_code, response.reason, body_text)
      raise errors.OrchestrationApiError(
          f"{method} {url} failed: {message}", code=code
      )
    return body_text


def _NormalizeBaseUrl(endpoint: str, api_version: str = API_VERSION) -> str:
  """Returns `<endpoint>/<api_version>` without duplicate slashes."""
  cleaned = endpoint.strip().rstrip("/")
  if cleaned.endswith(("/v1alpha", "/v1main", f"/{api_version}")):
    return cleaned
  return f"{cleaned}/{api_version}"


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


def _BuildRequestUrl(
    base_url: str,
    path: str,
    params: Mapping[str, str] | None = None,
) -> str:
  """Builds the full request URL with optional sorted query parameters."""
  url = f"{base_url}/{path.lstrip('/')}"
  if params:
    query = urllib_parse.urlencode(sorted(params.items()))
    return f"{url}?{query}"
  return url


def _BuildRequestPayload(
    body: Mapping[str, Any] | None,
) -> tuple[dict[str, str], str | None]:
  """Builds HTTP headers and serialized JSON body for a request."""
  headers = {"Accept": "application/json"}
  if body is None:
    return headers, None
  headers["Content-Type"] = "application/json"
  return headers, _ToCompactJson(body)


def _ToCompactJson(value: Any) -> str:
  """Serializes `value` as deterministic compact JSON."""
  return json.dumps(value, separators=(",", ":"), sort_keys=True, default=str)


def _DecodeResponseText(response: Any) -> str:
  """Returns the decoded text body of an HTTP `response`."""
  if isinstance(response.text, str):
    return response.text
  content = response.content
  if isinstance(content, bytes):
    return content.decode("utf-8", errors="replace")
  if isinstance(content, str):
    return content
  return ""


def _ParseJsonResponse(
    method: str, url: str, body_text: str
) -> dict[str, Any]:
  """Parses a JSON object response body, returning `{}` if empty."""
  stripped = body_text.strip()
  if not stripped:
    return {}
  try:
    parsed = json.loads(stripped)
  except ValueError as e:
    raise errors.OrchestrationApiError(
        f"{method} {url} returned a reply that is not JSON: {stripped}"
    ) from e
  if not isinstance(parsed, Mapping):
    raise errors.OrchestrationApiError(
        f"{method} {url} returned a JSON reply that is not an object:"
        f" {stripped}"
    )
  return dict(parsed)


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
