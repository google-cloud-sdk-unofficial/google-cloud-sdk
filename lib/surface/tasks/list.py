# Copyright 2017 Google Inc. All Rights Reserved.
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
"""`gcloud tasks queues describe` command."""

from googlecloudsdk.api_lib.tasks import tasks
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import parsers


_FORMAT = '''table(
    name.basename():label="TASK_NAME",
    tasktype():label=TYPE,
    createTime,
    scheduleTime,
    taskStatus.attemptDispatchCount.yesno(no="0"):label="DISPATCH_ATTEMPTS",
    taskStatus.attemptResponseCount.yesno(no="0"):label="RESPONSE_ATTEMPTS",
    taskStatus.lastAttemptStatus.responseStatus.message.yesno(no="Unknown")
        :label="LAST_ATTEMPT_STATUS")'''


def _IsPullTask(r):
  return 'pullTaskTarget' in r or 'pullMessage' in r


def _IsAppEngineTask(r):
  return 'appEngineTaskTarget' in r or 'appEngineHttpRequest' in r


def _TranformTaskType(r):
  if _IsPullTask(r):
    return constants.PULL_QUEUE
  if _IsAppEngineTask(r):
    return constants.APP_ENGINE_QUEUE


class List(base.ListCommand):
  """List tasks."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddTransforms({'tasktype': _TranformTaskType})
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(parsers.TasksUriFunc)
    parsers.AddQueueResourceFlag(parser, plural_tasks=True)

  def Run(self, args):
    tasks_client = tasks.Tasks()
    queue_ref = parsers.ParseQueue(args.queue)
    return tasks_client.List(queue_ref, args.limit, args.page_size)
