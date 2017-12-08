# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml-engine jobs stream-logs command."""
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.command_lib.ml import jobs_util
from googlecloudsdk.command_lib.ml import log_utils


def _AddStreamLogsArgs(parser):
  flags.JOB_NAME.AddToParser(parser)
  flags.POLLING_INTERVAL.AddToParser(parser)
  flags.ALLOW_MULTILINE_LOGS.AddToParser(parser)
  flags.TASK_NAME.AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class StreamLogsGa(base.Command):
  """Show logs from a running Cloud ML Engine job."""

  @staticmethod
  def Args(parser):
    _AddStreamLogsArgs(parser)

  def Run(self, args):
    """Run the stream-logs command."""
    return jobs_util.StreamLogs('v1', args.job, args.task_name,
                                args.polling_interval,
                                args.allow_multiline_logs)

  def Format(self, args):
    return log_utils.LOG_FORMAT


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class StreamLogsBeta(base.Command):
  """Show logs from a running Cloud ML Engine job."""

  @staticmethod
  def Args(parser):
    _AddStreamLogsArgs(parser)

  def Run(self, args):
    """Run the stream-logs command."""
    return jobs_util.StreamLogs('v1beta1', args.job, args.task_name,
                                args.polling_interval,
                                args.allow_multiline_logs)

  def Format(self, args):
    return log_utils.LOG_FORMAT
