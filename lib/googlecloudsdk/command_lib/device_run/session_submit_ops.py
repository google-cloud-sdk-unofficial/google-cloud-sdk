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
from typing import Any, Dict, List, Tuple
import uuid

from googlecloudsdk.api_lib import device_run
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.device_run import reports
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


def AddShardingFlags(parser: Any) -> None:
  """Adds common uniform and smart sharding flags to the command parser."""
  parser.add_argument(
      '--sharding-option',
      type=str,
      choices=['uniform', 'smart'],
      help=(
          'Specify the sharding strategy to partition the test execution'
          ' across multiple device allocations. Accepted values are `uniform`'
          ' or `smart`.'
      ),
  )
  parser.add_argument(
      '--uniform-sharding-count',
      type=int,
      help=(
          'Specify the total number of shards to create for uniform'
          ' sharding. Required when `--sharding-option=uniform`. The valid'
          ' range is `1` to `20` for physical devices and `1` to `200` for'
          ' virtual devices.'
      ),
  )
  parser.add_argument(
      '--smart-sharding-target-duration',
      type=arg_parsers.Duration(lower_bound='2m', upper_bound='1h'),
      help=(
          'Specify the targeted execution time (e.g., `2m`, `10m`, `1h`)'
          ' per shard for smart sharding. The valid range is `2m` to `1h`.'
          ' Required when `--sharding-option=smart`.'
      ),
  )
  parser.add_argument(
      '--smart-sharding-record-name',
      type=str,
      help=(
          'Specify the name of the smart sharding record file, excluding'
          ' the file extension. Required when `--sharding-option=smart`. This'
          ' file is located in the Google Cloud Storage bucket specified by'
          ' `--bucket-name` under the `automation/smart-sharding/` directory'
          ' with a `.yaml` extension. If the file does not exist, it will be'
          ' created automatically; otherwise, its contents will be updated'
          ' upon session completion.'
      ),
  )
  parser.add_argument(
      '--smart-sharding-max-shard-count',
      type=int,
      help=(
          'Specify the maximum number of shards to create for smart'
          ' sharding. If unset or set to 0, system-defined max limits are'
          ' used. The valid range is `0` to `20` for physical devices and'
          ' `0` to `200` for virtual devices.'
      ),
  )


def ValidateShardingArgs(args: Any) -> None:
  """Validates cross-flag dependencies for uniform and smart sharding flags."""
  if args.sharding_option == 'uniform' and args.uniform_sharding_count is None:
    raise calliope_exceptions.RequiredArgumentException(
        '--uniform-sharding-count',
        'Required when --sharding-option is uniform.',
    )
  if (
      args.uniform_sharding_count is not None
      and args.sharding_option != 'uniform'
  ):
    raise calliope_exceptions.InvalidArgumentException(
        '--uniform-sharding-count',
        'Can only be specified when --sharding-option is uniform.',
    )
  if (
      args.sharding_option == 'smart'
      and args.smart_sharding_target_duration is None
  ):
    raise calliope_exceptions.RequiredArgumentException(
        '--smart-sharding-target-duration',
        'Required when --sharding-option is smart.',
    )
  if (
      args.smart_sharding_target_duration is not None
      and args.sharding_option != 'smart'
  ):
    raise calliope_exceptions.InvalidArgumentException(
        '--smart-sharding-target-duration',
        'Can only be specified when --sharding-option is smart.',
    )
  if (
      args.sharding_option == 'smart'
      and args.smart_sharding_record_name is None
  ):
    raise calliope_exceptions.RequiredArgumentException(
        '--smart-sharding-record-name',
        'Required when --sharding-option is smart.',
    )
  if (
      args.smart_sharding_record_name is not None
      and args.sharding_option != 'smart'
  ):
    raise calliope_exceptions.InvalidArgumentException(
        '--smart-sharding-record-name',
        'Can only be specified when --sharding-option is smart.',
    )
  if (
      args.smart_sharding_max_shard_count is not None
      and args.sharding_option != 'smart'
  ):
    raise calliope_exceptions.InvalidArgumentException(
        '--smart-sharding-max-shard-count',
        'Can only be specified when --sharding-option is smart.',
    )


def BuildShardingOptions(
    args: Any, bucket_name: str, messages: Any
) -> Tuple[Any, Any]:
  """Builds (uniform_sharding, smart_sharding) proto messages from CLI args."""
  uniform_sharding = None
  smart_sharding = None
  if args.sharding_option == 'uniform':
    uniform_sharding = messages.UniformSharding(
        shardCount=args.uniform_sharding_count
    )
  elif args.sharding_option == 'smart':
    record_path = (
        f'gs://{bucket_name}/automation/smart-sharding/'
        f'{args.smart_sharding_record_name}.yaml'
    )
    smart_sharding = messages.SmartSharding(
        targetedShardDuration=f'{args.smart_sharding_target_duration}s',
        timingRecord=messages.InputFile(
            gcsInputFile=messages.GcsPath(path=record_path)
        ),
        maxShardCount=args.smart_sharding_max_shard_count,
    )
  return uniform_sharding, smart_sharding


def GetRunId() -> str:
  """Generates a run ID based on current timestamp and random suffix."""
  timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M.%S%f')
  random_suffix = uuid.uuid4().hex[:4].upper()
  return f'{timestamp}_{random_suffix}'


# Prefix used by the server when it generates a session ID. Client-generated
# IDs use the same format so that session names look the same no matter who
# generated them.
_SESSION_ID_PREFIX = 'session-'


def GenerateSessionAndRequestIds() -> Tuple[str, str]:
  """Returns a (session_id, request_id) pair for a CreateSession request.

  Passing only a `request_id` is not enough to make CreateSession idempotent:
  when `session_id` is omitted the server generates a new one for every request
  it processes, so a transparently retried request (for example after a
  transient 5xx or a lost response) targets a different session name than the
  original one. The API frontend then rejects the retry with "attempted to reuse
  'request_id' for incompatible requests" even though the first attempt
  succeeded.

  Sending a client-generated `session_id` alongside the `request_id` keeps the
  target resource name stable across retries, so a retry returns the original
  operation instead of failing.

  Returns:
    A tuple of (session_id, request_id).
  """
  request_id = str(uuid.uuid4())
  # Mirror the server-side format. Deriving both IDs from the same UUID also
  # makes it easy to correlate a session with the request that created it.
  session_id = f'{_SESSION_ID_PREFIX}{request_id}'
  return session_id, request_id


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
