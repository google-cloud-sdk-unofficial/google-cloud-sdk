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
"""Common operations for Device Run session submission."""

import datetime
import os
from typing import Any, Dict, List
import uuid

from googlecloudsdk.api_lib import device_run
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.device_run import reports
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


def GetRunId() -> str:
  """Generates a run ID based on current timestamp and random suffix."""
  timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M.%S%f')
  random_suffix = uuid.uuid4().hex[:4].upper()
  return f'{timestamp}_{random_suffix}'


def UploadFileIfNeeded(
    path: str, bucket_name: str, storage_client: Any, run_id: str
) -> str:
  """Uploads a local file to GCS if it is not already a GCS path."""
  if path.startswith('gs://'):
    return path
  log.status.Print(f'Uploading [{path}].')
  target_gcs_path = (
      f'gs://{bucket_name}/automation/inputs/{run_id}/{os.path.basename(path)}'
  )
  target_obj_ref = storage_util.ObjectReference.FromUrl(target_gcs_path)
  storage_client.CopyFileToGCS(path, target_obj_ref)
  return target_gcs_path


def GetDefaultBucketName(project_id: str) -> str:
  """Returns the default bucket name for the current project.

  Args:
    project_id: The Google Cloud project ID.

  Returns:
    GCS bucket name.
  """
  safe_project = (
      project_id.replace(':', '-').replace('.', '-').replace('google', 'elgoog')
  )

  return safe_project + '-devicerun'


def WaitForSession(
    client: Any, operation: Any, session_name: str
) -> List[Dict[str, Any]]:
  """Waits for the session LRO to complete and returns report rows."""
  session_id = session_name.split('/')[-1]
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name,
      collection='devicerun.projects.locations.operations',
  )
  operations_client = device_run.OperationsClient(api_version='v1alpha')
  poller = device_run.DeviceRunOperationPoller(
      resource_service=client.service,
      operations_service=operations_client.service,
      resource_ref=None,
  )
  device_run.WaitForOperation(
      poller,
      operation_ref,
      f'Waiting for session [{session_id}] to complete.',
  )
  session_ref = resources.REGISTRY.ParseRelativeName(
      session_name,
      collection='devicerun.projects.locations.sessions',
  )
  session = client.Get(session_ref)
  result_type = (
      session.sessionReport.result.resultType
      if session.sessionReport and session.sessionReport.result
      else None
  )
  rows = reports.ExtractSessionReportRows(session.sessionReport)

  # Print a blank line for spacing.
  log.status.Print()
  log.status.Print(
      f'Session [{session_id}] finished with result [{result_type}].'
  )

  return rows


def PrintResultFilesLink(
    gcs_uri: str, session_id: str, is_completed: bool = True
):
  """Prints the link to the GCS bucket where result files are stored.

  Args:
    gcs_uri: The GCS URI (e.g. 'gs://bucket/path').
    session_id: The session ID.
    is_completed: Whether the session is completed (changes the message tense).
  """
  if not gcs_uri:
    return
  try:
    ref = storage_util.ObjectReference.FromUrl(gcs_uri, allow_empty_object=True)
  except ValueError:
    gcs_path = gcs_uri
    if gcs_path.startswith('gs://'):
      gcs_path = gcs_path[5:]
    gcs_path = gcs_path.rstrip('/')
  else:
    if ref.name:
      gcs_path = f'{ref.bucket}/{ref.name}'.rstrip('/')
    else:
      gcs_path = ref.bucket

  message_prefix = (
      'Result files are stored at'
      if is_completed
      else 'Result files will be stored at'
  )

  log.status.Print(
      f'{message_prefix}'
      f' [https://console.cloud.google.com/storage/browser/{gcs_path}/{session_id}/].'
  )

