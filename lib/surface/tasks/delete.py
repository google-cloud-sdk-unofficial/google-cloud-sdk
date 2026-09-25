# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""`gcloud tasks delete` command."""

import json

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


# The BatchDeleteTasks API rejects requests with more than 1000 tasks, so larger
# requests are split into chunks of this size.
_MAX_TASKS_PER_BATCH = 1000

# Reported when an HTTP error carries no parseable status code.
_UNKNOWN_HTTP_STATUS_CODE = 500


def _HttpErrorStatusCode(error):
  """Returns the HTTP status code of error as an int."""
  try:
    return int(getattr(error, 'status_code', None))
  except (KeyError, TypeError, ValueError):
    # apitools resolves HttpError.status_code as int(self.response['status']),
    # which raises KeyError when the response carries no status.
    return _UNKNOWN_HTTP_STATUS_CODE


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a task from a queue."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          {description}
          """
      ),
      'EXAMPLES': (
          """\
          To delete a task:

              $ {command} --queue=my-queue my-task
         """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.AddTaskResourceArgs(parser, 'to delete')
    flags.AddLocationFlag(parser)

  def Run(self, args):
    tasks_client = GetApiAdapter(self.ReleaseTrack()).tasks
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    task_ref = parsers.ParseTask(args.task, queue_ref)
    tasks_client.Delete(task_ref)
    log.DeletedResource(task_ref.Name(), kind='task')


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaDelete(base.DeleteCommand):
  """Delete a task or multiple tasks from a queue."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          {description}
          """
      ),
      'EXAMPLES': (
          """\
          To delete a task:

              $ {command} --queue=my-queue my-task

          To delete multiple tasks:

              $ {command} --queue=my-queue task1 task2 task3
         """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.AddTaskResourceArgs(parser, 'to delete', required=False)
    flags.AddBatchDeleteTaskFlags(parser)
    flags.AddLocationFlag(parser)

  def Run(self, args):
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    task_refs, skipped_tasks = parsers.ParseTasksFromDeleteArgs(args, queue_ref)

    if (
        len(task_refs) == 1
        and not getattr(args, 'from_file', None)
        and not skipped_tasks
    ):
      tasks_client = GetApiAdapter(self.ReleaseTrack()).tasks
      tasks_client.Delete(task_refs[0])
      log.DeletedResource(task_refs[0].Name(), kind='task')
      return

    # Only the batch path needs a parent queue, which BatchDeleteTasks requires
    # even when `--queue` is omitted and tasks are given as full resource names.
    queue_ref = parsers.ResolveBatchDeleteQueue(queue_ref, task_refs)

    if not args.quiet:
      count = len(task_refs)
      count_str = '1 task' if count == 1 else '{} tasks'.format(count)
      console_io.PromptContinue(
          'Are you sure you want to delete {}?'.format(count_str),
          cancel_on_no=True,
      )

    api_adapter = GetApiAdapter(self.ReleaseTrack())
    tasks_client = api_adapter.tasks

    successful_refs = []
    api_failed_refs = []

    def _RecordChunkFailure(batch_chunk, start_index, err):
      """Records a failure that applies to every task in batch_chunk.

      A chunk can hold up to _MAX_TASKS_PER_BATCH tasks, so a single summary is
      logged instead of one error per task. Every task is still recorded in
      api_failed_refs so --failed-tasks-file and the exit code stay accurate.

      Args:
        batch_chunk: list of task references sent in the failed request.
        start_index: index of the chunk's first task within task_refs.
        err: dict describing the error that failed the whole chunk.
      """
      log.error(
          'Failed to delete batch of {} tasks starting at task {}: {}'.format(
              len(batch_chunk), start_index + 1, err['message']
          )
      )
      for task_ref in batch_chunk:
        api_failed_refs.append((task_ref, err))
        log.debug(
            'Failed to delete task [{}]: {}'.format(
                task_ref.Name(), err['message']
            )
        )

    for i in range(0, len(task_refs), _MAX_TASKS_PER_BATCH):
      batch_chunk = task_refs[i : i + _MAX_TASKS_PER_BATCH]

      try:
        operation = tasks_client.BatchDeleteTasks(queue_ref, batch_chunk)
      except NotImplementedError as e:
        raise exceptions.Error(str(e))
      except apitools_exceptions.HttpError as e:
        _RecordChunkFailure(
            batch_chunk,
            i,
            {
                'code': _HttpErrorStatusCode(e),
                'message': str(api_exceptions.HttpException(e)),
            },
        )
        continue

      metadata_dict = {}
      if operation and operation.metadata:
        metadata_dict = encoding.MessageToPyValue(operation.metadata) or {}

      failed_requests = (
          metadata_dict.get('failedRequests')
          or metadata_dict.get('failed_requests')
          or {}
      )

      if operation and operation.error and not failed_requests:
        _RecordChunkFailure(
            batch_chunk,
            i,
            {
                'code': getattr(operation.error, 'code', None),
                'message': (
                    operation.error.message or 'Batch delete operation failed.'
                ),
            },
        )
      else:
        # Indexes in failedRequests are relative to the chunk that was sent.
        for idx, task_ref in enumerate(batch_chunk):
          err = failed_requests.get(idx) or failed_requests.get(str(idx))
          if err is not None:
            api_failed_refs.append((task_ref, err))
            err_msg = err.get('message') if isinstance(err, dict) else str(err)
            log.error(
                'Failed to delete task [{}]: {}'.format(
                    task_ref.Name(), err_msg
                )
            )
          else:
            successful_refs.append(task_ref)

    total_count = len(task_refs) + len(skipped_tasks)
    success_count = len(successful_refs)
    failed_count = len(api_failed_refs) + len(skipped_tasks)

    if success_count > 0:
      log.DeletedResource(
          '{}/{}'.format(success_count, total_count), kind='tasks'
      )

    for item, reason in skipped_tasks:
      log.error('Skipped invalid task [{}]: {}'.format(item, reason))

    failed_tasks_file = getattr(args, 'failed_tasks_file', None)
    if failed_tasks_file:
      failed_records = []
      for task_ref, err in api_failed_refs:
        if isinstance(err, dict):
          err_obj = {
              'code': err.get('code'),
              'message': err.get('message'),
          }
          if 'status' in err:
            err_obj['status'] = err['status']
        else:
          err_obj = {'message': str(err)}
        failed_records.append({
            'task': task_ref.RelativeName(),
            'error': err_obj,
        })
      for item, reason in skipped_tasks:
        failed_records.append({
            'task': str(item),
            'error': {
                'code': 400,
                'message': reason,
            },
        })
      files.WriteFileContents(
          failed_tasks_file, json.dumps(failed_records, indent=2)
      )

    exit_code = parsers.DetermineBatchExitCode(failed_count, total_count)

    failure_file_suffix = ''
    if failed_tasks_file:
      failure_file_suffix = ' Review {} for error details.'.format(
          failed_tasks_file
      )

    if exit_code == 2:
      raise exceptions.Error(
          'Batch delete partially succeeded. {} of {} tasks failed to'
          ' delete.{}'.format(failed_count, total_count, failure_file_suffix),
          exit_code=2,
      )
    elif exit_code == 1:
      if total_count == 1:
        msg = 'Batch delete failed. 1 task failed to delete.{}'.format(
            failure_file_suffix
        )
      else:
        msg = 'Batch delete failed. All {} tasks failed to delete.{}'.format(
            total_count, failure_file_suffix
        )
      raise exceptions.Error(msg, exit_code=1)


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaDelete(BetaDelete):
  """Delete a task or multiple tasks from a queue."""
