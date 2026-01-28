# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""'logging saved_queries create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': (
        """
        Create a saved query.
    """
    ),
    'EXAMPLES': (
        """
     To create a saved query in a project, run:

        $ {command} --id=my-saved-query --location=global --display-name="My saved query" --visibility=private --sql-query-text="SELECT * FROM my_table"
    """
    ),
}


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Logging saved query."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('--id', help='ID of the saved query to create.')
    parser.add_argument(
        '--description', help='A textual description for the saved query.'
    )
    parser.add_argument(
        '--display-name',
        required=True,
        help='Display name for the saved query.',
    )
    parser.add_argument(
        '--visibility',
        required=True,
        choices=['private', 'shared'],
        help='Visibility of the saved query.',
    )
    util.AddParentArgs(parser, 'saved query to create')
    util.AddBucketLocationArg(
        parser, True, 'Location to create the saved query in.'
    )

    query_group = parser.add_group(mutex=True, required=True)
    query_group.add_argument('--sql-query-text', help='SQL query text.')
    log_query_group = query_group.add_group()
    log_query_group.add_argument(
        '--filter', help='Filter expression for the log-based query.'
    )
    log_query_group.add_argument(
        '--summary-fields',
        help=(
            'Comma-separated list of fields to include in the summary. This'
            ' flag must be specified if --summary-field-start or'
            ' --summary-field-end are provided.'
        ),
    )
    summary_field_group = log_query_group.add_group(mutex=True)
    summary_field_group.add_argument(
        '--summary-field-start',
        help=(
            'Setting for number of characters to display for each summary'
            ' field: characters will be counted from the start of the string.'
            ' Requires the --summary-fields flag to be specified as well.'
        ),
    )
    summary_field_group.add_argument(
        '--summary-field-end',
        help=(
            'Setting for number of characters to display for each summary'
            ' field: characters will be counted from the end of the string.'
            ' Requires the --summary-fields flag to be specified as well.'
        ),
    )

  def Run(self, args):
    """Creates a new saved query.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Saved query creation operation.
    """
    messages = util.GetMessages()
    saved_query_data = {}
    if args.description:
      saved_query_data['description'] = args.description
    if args.display_name:
      saved_query_data['displayName'] = args.display_name
    if args.visibility:
      saved_query_data['visibility'] = (
          messages.SavedQuery.VisibilityValueValuesEnum(args.visibility.upper())
      )

    if args.sql_query_text:
      saved_query_data['opsAnalyticsQuery'] = messages.OpsAnalyticsQuery(
          sqlQueryText=args.sql_query_text
      )
    else:
      logging_query_data = {}
      if args.filter:
        logging_query_data['filter'] = args.filter
      if args.summary_fields:
        logging_query_data['summaryFields'] = [
            messages.SummaryField(field=field)
            for field in args.summary_fields.split(',')
        ]
      if args.summary_field_start:
        logging_query_data['summaryFieldStart'] = args.summary_field_start
      if args.summary_field_end:
        logging_query_data['summaryFieldEnd'] = args.summary_field_end
      if logging_query_data:
        saved_query_data['loggingQuery'] = messages.LoggingQuery(
            **logging_query_data
        )

    client = util.GetClient()
    created_resource = client.projects_locations_savedQueries.Create(
        messages.LoggingProjectsLocationsSavedQueriesCreateRequest(
            parent=util.GetParentFromArgs(args) + '/locations/' + args.location,
            savedQueryId=args.id,
            savedQuery=messages.SavedQuery(**saved_query_data),
        )
    )

    log.CreatedResource(created_resource.name, 'saved query')
    return created_resource


Create.detailed_help = DETAILED_HELP
