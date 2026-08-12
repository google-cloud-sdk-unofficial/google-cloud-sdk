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
"""Command to query Dataplex Catalog using SQL."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def _GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'dataplex.projects.locations',
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=resource_args.LocationAttributeConfig(),
  )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Query(base.Command):
  """Query Dataplex Catalog using SQL.

  Retrieves metadata from the Dataplex Catalog using an SQL query.

  Output is rendered as YAML by default. Pass `--format=table` to dynamically
  format the resulting rows as a table.
  """

  detailed_help = {
      'EXAMPLES': (
          """\
          To query all rows from a table in us-central1, run:

            $ {command} --project=test-project --location=us-central1 --query="SELECT * FROM entries"
          """
      ),
      'API REFERENCE': (
          """\
          This command uses the dataplex/v1 API. The full documentation for this
          API can be found at: https://cloud.google.com/dataplex/docs
          """
      ),
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser.ForResource(
        '--location',
        _GetLocationResourceSpec(),
        'The location for the query.',
        required=False,
    ).AddToParser(parser)
    group = parser.add_argument_group(mutex=True, required=True)
    group.add_argument('--query', help='The SQL query string.')
    group.add_argument(
        '--reference-id',
        help='The reference ID from a previous query to fetch results.',
    )
    parser.add_argument(
        '--scopes',
        type=arg_parsers.ArgList(),
        metavar='SCOPE',
        help=(
            'One "organizations/<org>" or multiple "projects/<project>" '
            '(e.g., "projects/my-project1,projects/my-project2"). '
            'Providing a mixture, or more than one org is an error. '
            'If not provided, the default scope is the current project.'
        ),
    )
    parser.add_argument(
        '--timeout',
        type=arg_parsers.Duration(lower_bound='10s', upper_bound='200s'),
        help='The timeout for query execution. Default 10s, min 10s, max 200s.',
    )
    parser.add_argument(
        '--page-token',
        help=(
            'Page token received from a previous QueryCatalog call. Provide '
            'this together with the referenceId parameter to retrieve the '
            'subsequent page.'
        ),
    )
    parser.add_argument(
        '--max-results',
        type=int,
        help=(
            'The maximum number of rows of data to return per page of results. '
            'In addition to this limit, responses are also limited to 10 MB.'
        ),
    )

  def Run(self, args):
    client = apis.GetClientInstance('dataplex', 'v1')
    messages = apis.GetMessagesModule('dataplex', 'v1')
    location_ref = args.CONCEPTS.location.Parse()

    timeout_str = f'{args.timeout}s' if args.timeout is not None else None

    request = messages.DataplexProjectsLocationsQueryCatalogRequest(
        name=location_ref.RelativeName(),
        googleCloudDataplexV1QueryCatalogRequest=messages.GoogleCloudDataplexV1QueryCatalogRequest(
            query=args.query,
            referenceId=args.reference_id,
            scopes=args.scopes or [],
            timeout=timeout_str,
            maxResults=args.max_results,
            pageToken=args.page_token,
        ),
    )

    # If the user explicitly requested --format=table, gcloud's display parser
    # will bypass our Display() override and try to format the response message
    # itself, which throws an empty projection error because the response object
    # doesn't map correctly without our manual interception. We set args.format
    # to None so the Display() method executes, where we safely handle 'table'.
    if getattr(args, 'format', None) == 'table':
      args.user_format_table = True
      args.format = None

    return client.projects_locations.QueryCatalog(request)

  def Display(self, args, result):
    import json  # pylint: disable=g-import-not-at-top
    from apitools.base.py import encoding  # pylint: disable=g-import-not-at-top
    from googlecloudsdk.core import log  # pylint: disable=g-import-not-at-top
    from googlecloudsdk.core.resource import resource_printer  # pylint: disable=g-import-not-at-top

    request_format = args.format if args.IsSpecified('format') else 'yaml'
    if getattr(args, 'user_format_table', False):
      request_format = 'table'

    if not getattr(result, 'done', True):
      log.status.Print(
          f'Query with reference ID [{getattr(result, "referenceId", "")}] is'
          ' still running.'
      )
      log.status.flush()
      if request_format == 'table':
        resource_printer.Print(result, 'yaml')
        return

    # Intercept table format to dynamically construct columns
    if request_format == 'table':
      query_result = getattr(result, 'queryResult', None)
      rows = getattr(query_result, 'rows', None) if query_result else None

      if not rows:
        log.status.Print('Query returned 0 rows.')
        log.status.flush()
        return

      # Flatten the row objects to Python dicts using MessageToJson because
      # MessageToDict fails to unpack `GoogleProtobufStruct` objects properly
      # and returns empty dicts (resulting in a blank projection).
      dict_rows = [json.loads(encoding.MessageToJson(row)) for row in rows]

      fmt = request_format
      if request_format == 'table':
        keys_dict = {}
        for row in dict_rows:
          keys_dict.update({k: None for k in row})
        keys = list(keys_dict.keys())
        escaped_keys = []
        for k in keys:
          if not k.replace('_', '').isalnum():
            # Escape double quotes and wrap in double quotes
            k = f'"{k.replace(chr(34), chr(92) + chr(34))}"'
          escaped_keys.append(k)
        fmt = 'table(' + ', '.join(escaped_keys) + ')'

      resource_printer.Print(dict_rows, fmt)

      next_page = getattr(query_result, 'nextPageToken', None)
      if next_page:
        log.warning(
            "Output is truncated. Use --page-token='%s' to retrieve the"
            ' next page.',
            next_page,
        )
      return

    # Pass raw response when explicit format is not intercepted.
    resource_printer.Print(result, request_format)
