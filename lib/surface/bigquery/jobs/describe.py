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

"""Implementation of gcloud bigquery jobs describe.
"""

from googlecloudsdk.api_lib.bigquery import bigquery
from googlecloudsdk.api_lib.bigquery import job_display
from googlecloudsdk.calliope import base


class JobsDescribe(base.DescribeCommand):
  """Shows information about a specified job.

  The job's job type, state, start time, duration, and number of bytes
  processed are displayed.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('job_id', help='The ID of the job to be described.')

  def Collection(self):
    return 'bigquery.jobs.describe'

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespeace, All the arguments that were provided to this
        command invocation.

    Raises:
      bigquery.Error: if error is reported by the backend.

    Returns:
      A Job message.
    """
    return job_display.Synthesize(
        [bigquery.Job.ResolveFromId(args.job_id).GetRaw()])
