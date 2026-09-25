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
"""`gcloud tasks batch-create` command."""

import json
import uuid
from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib import tasks
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


GetApiAdapter = tasks.GetApiAdapter
_MAX_TASKS_PER_BATCH = 100


def _ExtractFailedRequests(op):
  """Extracts failed requests map {int_index: (status_dict, error_message)} from operation metadata."""
  if not op or not op.metadata:
    return {}
  if isinstance(op.metadata, dict):
    metadata_dict = op.metadata
  else:
    try:
      metadata_dict = encoding.MessageToPyValue(op.metadata)
    except Exception:  # pylint: disable=broad-exception-caught
      metadata_dict = None
  if not isinstance(metadata_dict, dict):
    return {}
  failed_requests = (
      metadata_dict.get('failedRequests')
      or metadata_dict.get('failed_requests')
      or {}
  )
  results = {}
  for idx_key, status_dict in failed_requests.items():
    try:
      idx = int(idx_key)
    except (ValueError, TypeError):
      log.debug('Skipping unparseable failedRequest key: %s', idx_key)
      continue
    if isinstance(status_dict, dict):
      msg = status_dict.get('message') or str(status_dict)
      st_dict = status_dict
    else:
      msg = getattr(status_dict, 'message', None) or str(status_dict)
      st_dict = {'message': msg}
    results[idx] = (st_dict, msg)
  return results


def _ExtractCreatedTasks(op, task_message_type):
  """Extracts list of Task messages from operation response."""
  if not op or not op.response:
    return []
  if hasattr(op.response, 'tasks') and op.response.tasks:
    return list(op.response.tasks)
  if isinstance(op.response, dict):
    resp_dict = op.response
  else:
    try:
      resp_dict = encoding.MessageToPyValue(op.response)
    except Exception:  # pylint: disable=broad-exception-caught
      resp_dict = None
  if isinstance(resp_dict, dict) and 'tasks' in resp_dict:
    tasks_list = []
    for t in resp_dict['tasks']:
      if isinstance(t, dict):
        tasks_list.append(encoding.PyValueToMessage(task_message_type, t))
      else:
        tasks_list.append(t)
    return tasks_list
  return []


@base.UniverseCompatible
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class BatchCreate(base.CreateCommand):
  """Create multiple tasks from a file in a single batch operation."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To create multiple tasks from a JSON or YAML file:

              $ {command} --queue=my-queue --tasks-from-file=tasks.yaml
         """,
  }

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceFlag(parser, plural_tasks=True)
    flags.AddBatchCreateTaskFlags(parser)
    flags.AddLocationFlag(parser)

  def Run(self, args):
    api = GetApiAdapter(self.ReleaseTrack())
    tasks_client = api.tasks
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    task_protos = parsers.ParseBatchCreateTasksArgs(args, api.messages)
    for t in task_protos:
      if t.name:
        t.name = parsers.ParseTask(t.name, queue_ref).RelativeName()
    create_requests = [
        api.messages.CreateTaskRequest(
            parent=queue_ref.RelativeName(), task=t
        )
        for t in task_protos
    ]

    total_tasks = len(create_requests)

    if getattr(args, 'dry_run', False):
      log.status.Print(
          'Dry run successful: {} tasks parsed and validated for queue'
          ' [{}].'.format(total_tasks, queue_ref.RelativeName())
      )
      return task_protos

    created_tasks = []
    failed_tasks_records = []
    failed_tasks_count = 0

    def _LogError(msg, debug_msg=None):
      log.debug(debug_msg if debug_msg is not None else msg)
      log.error(msg)

    for i in range(0, total_tasks, _MAX_TASKS_PER_BATCH):
      batch_chunk = create_requests[i : i + _MAX_TASKS_PER_BATCH]
      chunk_size = len(batch_chunk)

      request_id = str(uuid.uuid4())
      try:
        op = tasks_client.BatchCreateTasks(
            queue_ref, batch_chunk, request_id=request_id
        )
        if op.error:
          if isinstance(op.error, dict):
            status_dict = op.error
          else:
            try:
              status_dict = encoding.MessageToPyValue(op.error)
            except Exception:  # pylint: disable=broad-exception-caught
              status_dict = {
                  'code': getattr(op.error, 'code', 13),
                  'message': getattr(op.error, 'message', str(op.error)),
              }
          err_msg = status_dict.get('message', str(status_dict))
          _LogError(
              'Failed to create batch of {} tasks starting at task {}: {}'
              .format(chunk_size, i + 1, err_msg)
          )
          for offset in range(chunk_size):
            global_idx = i + offset
            failed_tasks_records.append({
                'index': global_idx,
                'status': status_dict,
                'task': encoding.MessageToPyValue(
                    create_requests[global_idx].task
                ),
            })
            log.debug(
                'Failed to create task at index {}: {}'.format(
                    global_idx, err_msg
                )
            )
          failed_tasks_count += chunk_size
        else:
          chunk_failed_requests = _ExtractFailedRequests(op)
          for offset, (status_dict, err_msg) in chunk_failed_requests.items():
            global_idx = i + offset
            _LogError(
                'Failed to create task at index {}: {}'.format(
                    global_idx, err_msg
                )
            )
            failed_tasks_records.append({
                'index': global_idx,
                'status': status_dict,
                'task': encoding.MessageToPyValue(
                    create_requests[global_idx].task
                ),
            })
          failed_tasks_count += len(chunk_failed_requests)
          created_tasks.extend(_ExtractCreatedTasks(op, api.messages.Task))
      except Exception as e:  # pylint: disable=broad-exception-caught
        if isinstance(e, apitools_exceptions.HttpError):
          err_msg = str(api_exceptions.HttpException(e))
          status_code = 500
          if hasattr(e, 'response') and isinstance(e.response, dict):
            try:
              status_code = int(e.response.get('status', 500))
            except (ValueError, TypeError):
              status_code = 500
          else:
            try:
              status_code = int(e.status_code)
            except Exception:  # pylint: disable=broad-exception-caught
              status_code = 500
        else:
          err_msg = str(e)
          status_code = 500
        _LogError(
            'Failed to create batch of {} tasks starting at task {}: {}'.format(
                chunk_size, i + 1, err_msg
            )
        )
        status_dict = {'code': status_code, 'message': err_msg}
        for offset in range(chunk_size):
          global_idx = i + offset
          failed_tasks_records.append({
              'index': global_idx,
              'status': status_dict,
              'task': encoding.MessageToPyValue(
                  create_requests[global_idx].task
              ),
          })
          log.debug(
              'Failed to create task at index {}: {}'.format(
                  global_idx, err_msg
              )
          )
        failed_tasks_count += chunk_size

    if getattr(args, 'failed_tasks_file', None):
      files.WriteFileContents(
          args.failed_tasks_file,
          json.dumps(failed_tasks_records, indent=2),
      )

    success_tasks_count = total_tasks - failed_tasks_count

    if failed_tasks_count > 0:
      if success_tasks_count > 0:
        log.CreatedResource(
            '{}/{}'.format(success_tasks_count, total_tasks), kind='tasks'
        )
        log.error(
            'Batch task creation partially succeeded. {} of {} tasks failed to'
            ' create.'.format(failed_tasks_count, total_tasks)
        )
        self.exit_code = 2
        return created_tasks
      else:
        if total_tasks == 1:
          msg = 'Batch task creation failed. 1 task failed to create.'
        else:
          msg = (
              'Batch task creation failed. All {} tasks failed to'
              ' create.'.format(total_tasks)
          )
        raise exceptions.Error(msg, exit_code=1)

    log.CreatedResource('{}'.format(total_tasks), kind='tasks')
    return created_tasks
