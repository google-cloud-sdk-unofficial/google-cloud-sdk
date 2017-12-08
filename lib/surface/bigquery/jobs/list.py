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

"""Implementation of gcloud bigquery jobs list.
"""

from googlecloudsdk.api_lib.bigquery import bigquery
from googlecloudsdk.api_lib.bigquery import job_display
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class JobsList(base.ListCommand):
  """Lists all jobs in a particular project.

  By default, jobs in the current project are listed; this can be overridden
  with the gcloud --project flag. The job ID, job type, state, start time, and
  duration of all jobs in the project are listed.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    base.LIMIT_FLAG.SetDefault(parser, bigquery.DEFAULT_RESULTS_LIMIT)
    parser.add_argument(
        '--all-users',
        action='store_true',
        help=('Whether to display jobs owned by all users in the project. '
              'Default false (boolean)'))

  def Collection(self):
    return 'bigquery.jobs.list'

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespeace, All the arguments that were provided to this
        command invocation.

    Returns:
      an iterator over JobsValueListEntry messages
    """
    project = bigquery.Project(
        properties.VALUES.core.project.Get(required=True))
    return job_display.Synthesize(project.GetCurrentRawJobsListGenerator(
        all_users=args.all_users,
        max_results=args.limit or -1))
