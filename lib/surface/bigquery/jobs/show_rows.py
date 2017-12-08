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

"""Implementation of gcloud bigquery jobs show-rows.
"""

from googlecloudsdk.api_lib.bigquery import bigquery
from googlecloudsdk.calliope import base
from googlecloudsdk.core.console import console_io


class JobsShowRows(base.Command):
  """Displays selected rows in the result of a query job.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--limit',
        type=int,
        default=bigquery.DEFAULT_RESULTS_LIMIT,
        help='The maximum number of rows to display.')
    parser.add_argument(
        '--start-row',
        type=int,
        default=0,
        help='The number of rows to skip before showing table data.')
    parser.add_argument('job_id', help='The job ID of the asynchronous query.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace, All the arguments that were provided to this
        command invocation.

    Returns:
      A bigquery.QueryResults object.
    """
    job = bigquery.Job.ResolveFromId(args.job_id)
    return job.GetQueryResults(start_row=args.start_row, max_rows=args.limit)

  def Display(self, args, query_results):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that the command was run with.
      query_results: A bigquery.QueryResults object.
    """
    console_io.PrintExtendedList(query_results,
                                 query_results.GetColumnFetchers())

