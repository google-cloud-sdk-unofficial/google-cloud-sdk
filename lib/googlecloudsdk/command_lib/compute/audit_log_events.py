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
"""Reads Compute Engine audit log entries for one instance."""

from __future__ import annotations

import datetime
import typing
from typing import Any

from apitools.base.py import encoding
from googlecloudsdk.api_lib.logging import common
from googlecloudsdk.api_lib.logging import util as logging_util
from googlecloudsdk.generated_clients.apis.logging.v2 import logging_v2_messages

# Cloud Audit Logs log IDs: fixed identifiers, not API endpoints.
SYSTEM_EVENT_LOG_ID = (  # gcloud-disable-gdu-domain
    'cloudaudit.googleapis.com%2Fsystem_event'
)
ACTIVITY_LOG_ID = (  # gcloud-disable-gdu-domain
    'cloudaudit.googleapis.com%2Factivity'
)
LOG_TYPE_SYSTEM_EVENT = 'system_event'
LOG_TYPE_ACTIVITY = 'activity'
DEFAULT_LIMIT = 1000


class AuditEvent(typing.NamedTuple):
  """One Compute Engine audit log entry, flattened.

  Attributes:
    timestamp: LogEntry.timestamp, RFC3339 string as returned by the API.
    method_name: protoPayload.methodName.
    log_type: LOG_TYPE_SYSTEM_EVENT or LOG_TYPE_ACTIVITY, from LogEntry.logName.
    insert_id: LogEntry.insertId.
    principal_email: protoPayload.authenticationInfo.principalEmail.
    caller_ip: protoPayload.requestMetadata.callerIp.
    user_agent: protoPayload.requestMetadata.callerSuppliedUserAgent.
    status_message: protoPayload.status.message.
    operation_id: LogEntry.operation.id (Compute writes the operation on the
      LogEntry, not inside the AuditLog payload).
    operation_first: LogEntry.operation.first, False when absent.
    operation_last: LogEntry.operation.last, False when absent.
    resource_name: protoPayload.resourceName.
  """

  timestamp: str
  method_name: str
  log_type: str
  insert_id: str
  principal_email: str | None
  caller_ip: str | None
  user_agent: str | None
  status_message: str | None
  operation_id: str | None
  operation_first: bool
  operation_last: bool
  resource_name: str | None


def BuildInstanceFilter(
    project_id: str, instance_id: str, start_time: datetime.datetime
) -> str:
  """Builds the Cloud Logging filter for one instance's audit log entries.

  Args:
    project_id: Project that owns the instance and its audit logs.
    instance_id: Numeric instance ID, matched against
      resource.labels.instance_id.
    start_time: Timezone-aware UTC lower bound (inclusive) on
      LogEntry.timestamp.

  Returns:
    A Cloud Logging filter expression selecting the instance's System Event and
    Admin Activity audit log entries at or after start_time.

  Raises:
    ValueError: If start_time is naive or not in UTC. The timestamp is
      formatted with a literal trailing 'Z', so any other offset would silently
      shift the window.
  """
  if start_time.utcoffset() != datetime.timedelta(0):
    raise ValueError(
        'start_time must be timezone-aware UTC, got: {!r}'.format(start_time)
    )
  log_names = ' OR '.join(
      '"projects/{}/logs/{}"'.format(project_id, log_id)
      for log_id in (SYSTEM_EVENT_LOG_ID, ACTIVITY_LOG_ID)
  )
  return (
      'resource.type="gce_instance" AND '
      'resource.labels.instance_id="{instance_id}" AND '
      'logName=({log_names}) AND '
      'timestamp>="{start}"'
  ).format(
      instance_id=instance_id,
      log_names=log_names,
      start=logging_util.FormatTimestamp(start_time),
  )


def _LogType(log_name: str | None) -> str | None:
  """Maps a LogEntry.logName to a LOG_TYPE_* constant, or None if unknown."""
  if not log_name:
    return None
  if log_name.endswith(SYSTEM_EVENT_LOG_ID):
    return LOG_TYPE_SYSTEM_EVENT
  if log_name.endswith(ACTIVITY_LOG_ID):
    return LOG_TYPE_ACTIVITY
  return None


def _Get(payload: Any, *keys: str) -> Any:
  """Returns payload[keys[0]][keys[1]]..., or None if any step is missing."""
  value = payload
  for key in keys:
    if not isinstance(value, dict):
      return None
    value = value.get(key)
  return value


def _OperationFields(
    entry: logging_v2_messages.LogEntry,
) -> tuple[str | None, bool, bool]:
  """Returns (operation id, first, last) from LogEntry.operation.

  Args:
    entry: A logging v2 LogEntry message.

  Returns:
    A tuple of (LogEntry.operation.id or None, first, last); (None, False,
    False) when the entry has no operation.
  """
  operation = entry.operation
  if operation is None:
    return None, False, False
  return operation.id, bool(operation.first), bool(operation.last)


def ParseLogEntry(entry: logging_v2_messages.LogEntry) -> AuditEvent | None:
  """Converts one LogEntry into an AuditEvent.

  Args:
    entry: A logging v2 LogEntry message as yielded by common.FetchLogs.

  Returns:
    The AuditEvent, or None when the entry is not a Compute audit entry: no
    protoPayload, no protoPayload.methodName, or a logName that is neither the
    System Event nor the Admin Activity log. Missing optional payload fields
    yield None (bools yield False); a partial payload never raises.
  """
  log_type = _LogType(entry.logName)
  if log_type is None:
    return None
  proto_payload = entry.protoPayload
  if proto_payload is None:
    return None
  payload = encoding.MessageToDict(proto_payload)
  method_name = payload.get('methodName')
  if not method_name:
    return None
  operation_id, operation_first, operation_last = _OperationFields(entry)
  return AuditEvent(
      timestamp=entry.timestamp,
      method_name=method_name,
      log_type=log_type,
      insert_id=entry.insertId,
      principal_email=_Get(payload, 'authenticationInfo', 'principalEmail'),
      caller_ip=_Get(payload, 'requestMetadata', 'callerIp'),
      user_agent=_Get(payload, 'requestMetadata', 'callerSuppliedUserAgent'),
      status_message=_Get(payload, 'status', 'message'),
      operation_id=operation_id,
      operation_first=operation_first,
      operation_last=operation_last,
      resource_name=payload.get('resourceName'),
  )


def FetchInstanceAuditEvents(
    project_id: str,
    instance_id: str,
    start_time: datetime.datetime,
    limit: int = DEFAULT_LIMIT,
) -> list[AuditEvent]:
  """Fetches one instance's audit log entries from Cloud Logging.

  Reads the System Event and Admin Activity audit logs through
  common.FetchLogs, newest first, and returns the parsed rows oldest first.
  Entries that are not Compute audit entries (see ParseLogEntry) are dropped.

  This function does not catch apitools HttpError: the caller is responsible
  for handling permission-denied and API-not-enabled errors.

  Args:
    project_id: Project that owns the instance and its audit logs.
    instance_id: Numeric instance ID.
    start_time: Timezone-aware UTC lower bound (inclusive) on
      LogEntry.timestamp.
    limit: Maximum number of log entries to read from the API.

  Returns:
    AuditEvents in ascending timestamp order (the DESC page reversed, not
    re-sorted), at most `limit` of them.

  Raises:
    ValueError: If start_time is naive or not in UTC.
  """
  entries = common.FetchLogs(
      log_filter=BuildInstanceFilter(project_id, instance_id, start_time),
      order_by='DESC',
      limit=limit,
      parent='projects/{}'.format(project_id),
  )
  return [
      event for event in map(ParseLogEntry, entries) if event is not None
  ][::-1]
