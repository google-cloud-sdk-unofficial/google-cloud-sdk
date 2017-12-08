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
"""`gcloud tasks queues list` command."""

from googlecloudsdk.api_lib.tasks import queues
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import parsers


_FORMAT = '''table(
    name.basename():label="QUEUE_NAME",
    queuetype():label=TYPE,
    queueState:label=STATE,
    throttleConfig.maxOutstandingTasks.yesno(no="unlimited").format("{0}").sub("-1", "unlimited"):label="MAX_NUM_OF_TASKS",
    throttleConfig.maxTasksDispatchedPerSecond.yesno(no="unlimited"):label="MAX_RATE (/sec)",
    retryConfig.maxAttempts.yesno(no="unlimited"):label="MAX_ATTEMPTS")'''


def _IsPullQueue(r):
  return 'pullTarget' in r


def _IsAppEngineQueue(r):
  return 'appEngineHttpTarget' in r


def _TranformQueueType(r):
  if _IsPullQueue(r):
    return constants.PULL_QUEUE
  if _IsAppEngineQueue(r):
    return constants.APP_ENGINE_QUEUE


class List(base.ListCommand):
  """List all queues."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddTransforms({'queuetype': _TranformQueueType})
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(parsers.QueuesUriFunc)

  def Run(self, args):
    queues_client = queues.Queues()
    region_ref = parsers.ParseLocation(app.ResolveAppLocation())
    return queues_client.List(region_ref, args.limit, args.page_size)
