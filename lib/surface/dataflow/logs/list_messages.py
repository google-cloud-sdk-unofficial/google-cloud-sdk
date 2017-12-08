# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Implementation of gcloud dataflow logs list-messages command.
"""

from googlecloudsdk.api_lib.dataflow import job_utils
from googlecloudsdk.api_lib.dataflow import list_pager
from googlecloudsdk.api_lib.dataflow import time_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_projection_spec
from surface import dataflow as commands


class ListMessages(base.ListCommand):
  """Retrieve the logs from a specific job using the GetMessages RPC.

  This is intended for short-term use and will be removed once the CLI based on
  Cloud Logging is available.
  """

  @staticmethod
  def Args(parser):
    job_utils.ArgsForJobRef(parser)

    parser.add_argument(
        '--after', type=time_util.ParseTimeArg,
        help='Only display messages logged after the given time.')
    parser.add_argument(
        '--before', type=time_util.ParseTimeArg,
        help='Only display messages logged before the given time.')
    parser.add_argument(
        '--importance', choices=['debug', 'detailed', 'warning', 'error'],
        help='Minimum importance a message must have to be displayed',
        default='warning')

  def Collection(self):
    return 'dataflow.logs'

  def Defaults(self):
    importances = {
        'JOB_MESSAGE_DETAILED': 'd',
        'JOB_MESSAGE_DEBUG': 'D',
        'JOB_MESSAGE_WARNING': 'W',
        'JOB_MESSAGE_ERROR': 'E',
    }
    symbols = {'dataflow.JobMessage::enum': importances}
    return resource_projection_spec.ProjectionSpec(symbols=symbols)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: all the arguments that were provided to this command invocation.

    Returns:
      None on success, or a string containing the error message.
    """
    apitools_client = self.context[commands.DATAFLOW_APITOOLS_CLIENT_KEY]
    dataflow_messages = self.context[commands.DATAFLOW_MESSAGES_MODULE_KEY]
    job_ref = job_utils.ExtractJobRef(self.context, args)

    importance_enum = (
        dataflow_messages.DataflowProjectsJobsMessagesListRequest
        .MinimumImportanceValueValuesEnum)
    importance_map = {
        'debug': importance_enum.JOB_MESSAGE_DEBUG,
        'detailed': importance_enum.JOB_MESSAGE_DETAILED,
        'error': importance_enum.JOB_MESSAGE_ERROR,
        'warning': importance_enum.JOB_MESSAGE_WARNING,
    }

    request = dataflow_messages.DataflowProjectsJobsMessagesListRequest(
        projectId=job_ref.projectId,
        jobId=job_ref.jobId,
        minimumImportance=(args.importance and importance_map[args.importance]),

        # Note: It if both are present, startTime > endTime, because we will
        # return messages with actual time [endTime, startTime).
        startTime=args.before and time_util.Strftime(args.before),
        endTime=args.after and time_util.Strftime(args.after))

    return self._GetMessages(apitools_client, request)

  def _GetMessages(self, apitools_client, request):
    return list_pager.YieldFromList(
        apitools_client.projects_jobs_messages,
        request,
        batch_size=None,  # Use server default.
        field='jobMessages')
