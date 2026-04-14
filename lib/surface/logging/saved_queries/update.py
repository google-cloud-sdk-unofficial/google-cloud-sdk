# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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

"""'logging saved_queries update' command."""

import argparse

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.generated_clients.apis.logging.v2 import logging_v2_messages as messages

DETAILED_HELP = {
    'DESCRIPTION': (
        """\
        Update a saved query.
    """
    ),
    'EXAMPLES': (
        """\
        To update the display name and description of a saved query, run:

          $ {command} my-saved-query --display-name="New Name" --description="New Description"
    """
    ),
}


def _get_updated_summary_fields(
    args: argparse.Namespace, current_summary_fields: list[str]
) -> list[str]:
  """Calculates the new list of summary fields based on user arguments.

  Args:
    args: An argparse namespace with command-line arguments.
    current_summary_fields: The current list of summary fields.

  Returns:
    A list of updated summary fields.
  """
  if args.clear_summary_fields:
    new_summary_fields = []
  else:
    new_summary_fields = list(current_summary_fields)

  if args.add_summary_field:
    for field in args.add_summary_field:
      if field not in new_summary_fields:
        new_summary_fields.append(field)
  if args.remove_summary_field:
    for field in args.remove_summary_field:
      if field in new_summary_fields:
        new_summary_fields.remove(field)
  return new_summary_fields


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update Logging saved queries.

  Updates a saved query in Google Cloud Logging.
  """

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    """Registers flags for this command.

    Args:
      parser: An argparse.ArgumentParser object. The parser that will be used to
        parse the command line arguments.
    """
    parser.add_argument(
        'SAVED_QUERY_ID', help='ID of the saved query to update.'
    )

    util.AddParentArgs(parser, 'saved query to update')
    util.AddBucketLocationArg(parser, False, 'Location of the saved query.')
    parser.add_argument('--name', help='The resource name of the saved query.')

    parser.add_argument(
        '--display-name', help='The display name of the saved query.'
    )
    parser.add_argument(
        '--description', help='The description of the saved query.'
    )
    parser.add_argument(
        '--visibility', help='The visibility of the saved query.'
    )

    query_group = parser.add_group(mutex=True)
    query_group.add_argument(
        '--sql-query-text',
        help=(
            'The SQL query text. If this argument is specified, no '
            'LoggingQuery arguments (--log-filter, --add-summary-field, etc.) '
            'may be specified.'
        ),
    )

    ops_group = query_group.add_group()
    ops_group.add_argument(
        '--log-filter',
        help=(
            'The logging filter. If this argument is specified, '
            '--sql-query-text may not be specified.'
        ),
    )
    ops_group.add_argument(
        '--add-summary-field', action='append', help='Add a summary field.'
    )
    ops_group.add_argument(
        '--remove-summary-field',
        action='append',
        help='Remove a summary field.',
    )
    ops_group.add_argument(
        '--clear-summary-fields',
        action='store_true',
        help='Clear all summary fields.',
    )

    summary_range = ops_group.add_group(mutex=True)
    summary_range.add_argument(
        '--summary-field-start', type=int, help='Summary field start.'
    )
    summary_range.add_argument(
        '--summary-field-end', type=int, help='Summary field end.'
    )

  def Run(self, args: argparse.Namespace) -> messages.SavedQuery:
    """Updates a saved query using the Logging API.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated SavedQuery.
    """
    client = util.GetClient()
    location = args.location or 'global'
    resource_name = util.CreateResourceName(
        util.CreateResourceName(
            util.GetParentFromArgs(args), 'locations', location
        ),
        'savedQueries',
        args.SAVED_QUERY_ID,
    )

    saved_query_data = {}
    update_mask = []

    if args.IsSpecified('name'):
      saved_query_data['name'] = args.name
      update_mask.append('name')
    if args.IsSpecified('display_name'):
      saved_query_data['displayName'] = args.display_name
      update_mask.append('displayName')
    if args.IsSpecified('description'):
      saved_query_data['description'] = args.description
      update_mask.append('description')
    if args.IsSpecified('visibility'):
      saved_query_data['visibility'] = (
          messages.SavedQuery.VisibilityValueValuesEnum(args.visibility.upper())
      )
      update_mask.append('visibility')

    # The '--sql-query-text' argument and arguments for LoggingQuery
    # ('--log-filter', '--add-summary-field', etc.) are in a mutex group,
    # so they cannot be specified together.
    if args.IsSpecified('sql_query_text'):
      saved_query_data['opsAnalyticsQuery'] = messages.OpsAnalyticsQuery(
          sqlQueryText=args.sql_query_text
      )
      update_mask.append('opsAnalyticsQuery.sqlQueryText')
    else:
      logging_query_data = {}
      if args.IsSpecified('log_filter'):
        logging_query_data['filter'] = args.log_filter
        update_mask.append('loggingQuery.filter')
      if args.IsSpecified('summary_field_start'):
        logging_query_data['summaryFieldStart'] = args.summary_field_start
        update_mask.append('loggingQuery.summaryFieldStart')
      if args.IsSpecified('summary_field_end'):
        logging_query_data['summaryFieldEnd'] = args.summary_field_end
        update_mask.append('loggingQuery.summaryFieldEnd')
      if any([
          args.IsSpecified('add_summary_field'),
          args.IsSpecified('remove_summary_field'),
          args.IsSpecified('clear_summary_fields'),
      ]):
        current_saved_query = client.projects_locations_savedQueries.Get(
            messages.LoggingProjectsLocationsSavedQueriesGetRequest(
                name=resource_name
            )
        )
        current_summary_fields = []
        if (
            current_saved_query.loggingQuery
            and current_saved_query.loggingQuery.summaryFields
        ):
          current_summary_fields = [
              field.field
              for field in current_saved_query.loggingQuery.summaryFields
          ]

        new_summary_fields = _get_updated_summary_fields(
            args, current_summary_fields
        )

        logging_query_data['summaryFields'] = [
            messages.SummaryField(field=field) for field in new_summary_fields
        ]
        update_mask.append('loggingQuery.summaryFields')

      if logging_query_data:
        saved_query_data['loggingQuery'] = messages.LoggingQuery(
            **logging_query_data
        )

    return client.projects_locations_savedQueries.Patch(
        messages.LoggingProjectsLocationsSavedQueriesPatchRequest(
            name=resource_name,
            savedQuery=messages.SavedQuery(**saved_query_data),
            updateMask=','.join(update_mask),
        )
    )


Update.detailed_help = DETAILED_HELP
