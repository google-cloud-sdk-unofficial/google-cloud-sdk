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
"""Utility functions for BigQuery translation commands."""

import functools
import json
import os
import pkgutil
import typing

from googlecloudsdk.api_lib.bq import util as api_util
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.bq import command_utils
from googlecloudsdk.command_lib.storage import storage_parallel
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@functools.cache
def _get_dialect_registry():
  """Gets dialect registry: input_dialects, output_dialects, dialect_pairs.

  The mapping is loaded from a JSON resource file.

  Returns:
    A dict with dialect registry.

  Raises:
    exceptions.Error: If the dialect registry fails to load.
  """
  try:
    data = pkgutil.get_data(
        'surface.bq.translation', 'dialect_registry.json'
    )
    if data is None:
      raise exceptions.Error(
          'Could not read dialect_registry.json from package data.'
      )
    registry = json.loads(data.decode('utf-8'))
    return registry
  except Exception as e:
    raise exceptions.Error(f'Failed to load dialect registry: {e}')


def get_task_type(source_dialect: str, target_dialect: str) -> str:
  """Returns the translation task type based on the source dialect."""
  registry = _get_dialect_registry()
  source_dialect_map = {}
  for dialect in registry.get('input_dialects', []):
    legacy_name = dialect.get('legacy_batch_name')
    name = dialect.get('name')
    if legacy_name:
      if name:
        source_dialect_map[name.lower()] = legacy_name
      source_dialect_map[legacy_name.lower()] = legacy_name
    elif name:
      source_dialect_map[name.lower()] = name
  source_legacy_batch_name = source_dialect_map.get(
      source_dialect.lower(), source_dialect
  )
  target_dialect_map = {}
  for dialect in registry.get('output_dialects', []):
    legacy_name = dialect.get('legacy_batch_name')
    name = dialect.get('name')
    if legacy_name:
      if name:
        target_dialect_map[name.lower()] = legacy_name
      target_dialect_map[legacy_name.lower()] = legacy_name
    elif name:
      target_dialect_map[name.lower()] = name
  target_legacy_batch_name = target_dialect_map.get(
      target_dialect.lower(), target_dialect
  )
  task_type = (
      f'{source_legacy_batch_name}2{target_legacy_batch_name}_Translation'
  )
  valid_task_type = False
  for pair in registry['dialect_pairs']:
    if task_type in pair.get('legacy_batch_name', []):
      valid_task_type = True
      break
  if not valid_task_type:
    raise exceptions.Error(
        f'Translation from {source_dialect} to {target_dialect} is not'
        ' supported.'
    )
  return task_type


def _build_file_upload_tasks(
    local_path: str,
    target_uri: str,
    is_file: bool = False,
) -> list[storage_parallel.FileUploadTask]:
  """Constructs FileUploadTask objects for local files or directory tree.

  Args:
    local_path: The local directory or file path.
    target_uri: The destination Cloud Storage URI.
    is_file: Whether local_path is a single file.

  Returns:
    List of storage_parallel.FileUploadTask objects.

  Raises:
    calliope_exceptions.BadFileException: If local_path does not exist or is not
      the expected type.
  """
  if is_file:
    if not os.path.isfile(local_path):
      raise calliope_exceptions.BadFileException(
          f'[{local_path}] is not a valid file.'
      )
    dest_ref = storage_util.ObjectReference.FromUrl(target_uri)
    return [storage_parallel.FileUploadTask(local_path, dest_ref)]

  if not os.path.isdir(local_path):
    raise calliope_exceptions.BadFileException(
        f'[{local_path}] is not a valid directory.'
    )

  if not target_uri.endswith('/'):
    target_uri += '/'

  tasks = []
  for root, _, files in os.walk(local_path):
    for file in sorted(files):
      file_path = os.path.join(root, file)
      rel_path = os.path.relpath(file_path, local_path)
      rel_path = rel_path.replace(os.sep, '/')
      curr_target_uri = target_uri + rel_path
      dest_ref = storage_util.ObjectReference.FromUrl(curr_target_uri)
      tasks.append(storage_parallel.FileUploadTask(file_path, dest_ref))
  return tasks


def upload_local_files_to_gcs(
    local_path: str,
    target_uri: str,
    is_file: bool = False,
    num_threads: int = storage_parallel.DEFAULT_NUM_THREADS,
) -> None:
  """Uploads local files or a directory tree to a Cloud Storage URI.

  Args:
    local_path: The local directory or file path.
    target_uri: The destination Cloud Storage URI.
    is_file: Whether local_path is a single file.
    num_threads: Number of threads for parallel directory uploads.

  Raises:
    calliope_exceptions.BadFileException: If local_path does not exist or is not
      the expected type.
  """
  tasks = _build_file_upload_tasks(local_path, target_uri, is_file=is_file)
  if tasks:
    storage_parallel.UploadFiles(tasks, num_threads=num_threads)


def validate_target_gcs_path(target_gcs_path: str) -> None:
  """Validates that target_gcs_path is a valid Cloud Storage URI."""
  if not storage_util.ObjectReference.IsStorageUrl(target_gcs_path):
    raise calliope_exceptions.InvalidArgumentException(
        '--target-gcs-path',
        'Must be a valid Cloud Storage URI.',
    )


def validate_source_inputs_and_upload_local_files(
    source_gcs_uris: typing.Sequence[str],
    source_gcs_files: typing.Sequence[str],
    source_local_dirs: typing.Mapping[str, str],
    source_local_files: typing.Mapping[str, str],
) -> tuple[list[str], list[str]]:
  """Validates source inputs and uploads local files to Cloud Storage.

  Args:
    source_gcs_uris: List of Cloud Storage URI prefixes containing source files.
    source_gcs_files: List of Cloud Storage URIs pointing to individual files.
    source_local_dirs: Map of local directories to Cloud Storage destination
      URIs.
    source_local_files: Map of local files to Cloud Storage destination URIs.

  Returns:
    A tuple of (gcs_uris, gcs_files).

  Raises:
    calliope_exceptions.MinimumArgumentException: If no source inputs are
      specified.
  """
  if not (
      source_gcs_uris
      or source_gcs_files
      or source_local_dirs
      or source_local_files
  ):
    raise calliope_exceptions.MinimumArgumentException([
        '--source-gcs-uris',
        '--source-gcs-files',
        '--source-local-dirs',
        '--source-local-files',
    ])

  gcs_uris = list(source_gcs_uris)
  gcs_files = list(source_gcs_files)
  tasks_to_upload = []

  for local_d, gcs_u in source_local_dirs.items():
    if not gcs_u.endswith('/'):
      gcs_u += '/'
    tasks_to_upload.extend(
        _build_file_upload_tasks(local_d, gcs_u, is_file=False)
    )
    if gcs_u not in gcs_uris:
      gcs_uris.append(gcs_u)

  for local_f, gcs_f in source_local_files.items():
    tasks_to_upload.extend(
        _build_file_upload_tasks(local_f, gcs_f, is_file=True)
    )
    if gcs_f not in gcs_files:
      gcs_files.append(gcs_f)

  if tasks_to_upload:
    storage_parallel.UploadFiles(tasks_to_upload)

  return gcs_uris, gcs_files


def build_source_target_mappings(
    messages,
    gcs_uris: typing.Sequence[str],
    gcs_files: typing.Sequence[str],
) -> list[typing.Any]:
  """Builds a list of SourceTargetMapping messages from GCS URIs and files."""
  source_target_mapping = []
  target_spec = messages.GoogleCloudBigqueryMigrationV2TargetSpec()

  for base_uri in gcs_uris:
    source_target_mapping.append(
        messages.GoogleCloudBigqueryMigrationV2SourceTargetMapping(
            sourceSpec=messages.GoogleCloudBigqueryMigrationV2SourceSpec(
                baseUri=base_uri
            ),
            targetSpec=target_spec,
        )
    )

  for file_uri in gcs_files:
    source_target_mapping.append(
        messages.GoogleCloudBigqueryMigrationV2SourceTargetMapping(
            sourceSpec=messages.GoogleCloudBigqueryMigrationV2SourceSpec(
                gcsFilePath=file_uri
            ),
            targetSpec=target_spec,
        )
    )

  return source_target_mapping


def build_translation_details(
    messages,
    target_gcs_path: str,
    source_target_mapping: typing.Sequence[typing.Any],
    target_types: typing.Sequence[str],
):
  """Builds a TranslationDetails message."""
  return messages.GoogleCloudBigqueryMigrationV2TranslationDetails(
      targetBaseUri=target_gcs_path,
      sourceTargetMapping=list(source_target_mapping),
      targetTypes=list(target_types),
  )


def build_migration_workflow(messages, task_key: str, task):
  """Wraps a single MigrationTask into a MigrationWorkflow."""
  workflow_cls = messages.GoogleCloudBigqueryMigrationV2MigrationWorkflow
  prop_cls = workflow_cls.TasksValue.AdditionalProperty
  workflow_tasks_value = workflow_cls.TasksValue(
      additionalProperties=[prop_cls(key=task_key, value=task)]
  )
  return workflow_cls(tasks=workflow_tasks_value)


def get_migration_client(location=None):
  """Returns a BigQuery Migration API client configured with the gcloud tool-tag header."""
  if location:
    client = apis.GetClientInstance(
        'bigquerymigration', 'v2', location=location
    )
  else:
    client = api_util.GetMigrationApiClient()
  client.additional_http_headers[api_util.TOOL_TAG_HEADER] = (
      api_util.GCLOUD_TOOL_TAG
  )
  return client


def execute_workflow(
    migration_service,
    workflow_request,
    task_type: str,
    is_async: bool,
    location: str,
    operation_message: str = 'Running batch translation',
    completion_message: str = 'Batch translation workflow finished with state',
    workflow_type_label: str = 'batch translation',
) -> dict[str, typing.Any]:
  """Creates workflow and handles async response or sync waiter polling."""
  response = migration_service.Create(workflow_request)

  workflow_ref = resources.REGISTRY.ParseRelativeName(
      response.name,
      collection='bigquerymigration.projects.locations.workflows',
  )

  if is_async:
    translation_id = workflow_ref.Name()
    log.status.Print(
        'Translation request submitted successfully.\nTranslation ID:'
        f' {translation_id}\n\nTo check the status of this request,'
        f' run:\ngcloud bq translation describe {translation_id}'
        f' --location={location}'
    )
    if hasattr(response.state, 'name'):
      state = response.state.name
    elif response.state:
      state = str(response.state)
    else:
      state = 'PENDING'
    return {
        'name': response.name,
        'type': task_type,
        'state': state,
    }

  poller = command_utils.BqMigrationWorkflowPoller(migration_service)

  try:
    wait_response = waiter.WaitFor(
        poller=poller,
        operation_ref=workflow_ref,
        message=f'{operation_message} [{response.name}]',
    )
  except waiter.TimeoutError as exc:
    translation_id = workflow_ref.Name()
    raise waiter.TimeoutError(
        f'The {workflow_type_label} is taking longer than expected to complete'
        ' and has timed out locally. The operation may still be underway'
        f' remotely.\n\nTranslation ID: {translation_id}\n\nTo check the'
        ' status of this request, run:\ngcloud bq translation describe'
        f' {translation_id} --location={location}'
    ) from exc

  if hasattr(wait_response.state, 'name'):
    state = wait_response.state.name
  elif wait_response.state:
    state = str(wait_response.state)
  else:
    state = 'COMPLETED'
  log.status.Print(f'{completion_message}: {state}')
  log.status.Print(f'Translation ID: {workflow_ref.Name()}')

  return {
      'name': wait_response.name,
      'type': task_type,
      'state': state,
  }
