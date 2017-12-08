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
"""ml jobs showlogs command."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.logs import stream
from googlecloudsdk.command_lib.ml import flags


class StreamLogs(base.Command):
  """Show logs from a running Cloud ML job."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.JOB_NAME.AddToParser(parser)
    flags.POLLING_INTERVAL.AddToParser(parser)
    flags.ALLOW_MULTILINE_LOGS.AddToParser(parser)
    flags.TASK_NAME.AddToParser(parser)

  def Run(self, args):
    """Run the stream-logs command."""
    log_fetcher = stream.LogFetcher(job_id=args.job,
                                    polling_interval=args.polling_interval,
                                    allow_multiline_logs=
                                    args.allow_multiline_logs,
                                    task_name=args.task_name)
    return log_fetcher.YieldLogs()

  def Format(self, args):
    """Returns the default formatting for the command.

    This overrides the base.Command method of the same name.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    return stream.LogFetcher.LOG_FORMAT
