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
"""Command for executing BigQuery queries."""

from googlecloudsdk.api_lib.bq import util as api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bq import query_utils
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.RegionalEndpointsSupported
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Query(base.Command):
  """Execute a BigQuery SQL query."""

  detailed_help = {
      'brief': 'Execute a BigQuery SQL query.',
      'DESCRIPTION': (
          """\
          *{command}* executes a SQL query on Google Cloud BigQuery.

          The query can be passed as a positional argument or read from
          standard input (stdin).
          """
      ),
      'EXAMPLES': (
          """\
          To execute a simple query:

            $ {command} 'SELECT 1'

          To execute a query passed through stdin:

            $ echo 'SELECT 1' | {command}

          To run a query asynchronously with a custom job ID:

            $ {command} 'SELECT 1' --async --job-id=my-job-id
          """
      ),
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'sql_query',
        nargs='?',
        help=(
            'SQL query to execute. If not specified, query will be read from'
            ' stdin.'
        ),
    )
    parser.add_argument(
        '--job-creation-mode',
        choices=['JOB_CREATION_REQUIRED', 'JOB_CREATION_OPTIONAL'],
        type=arg_utils.ChoiceToEnumName,
        default=None,
        help='Specifies whether a job should be created.',
    )
    parser.add_argument(
        '--job-id',
        help=(
            'A unique job ID to use for the query job. Forces a job to be'
            ' created and is incompatible with'
            ' `--job-creation-mode=JOB_CREATION_OPTIONAL`.'
        ),
    )
    parser.add_argument(
        '--location',
        help='The geographic location where the query should run.',
    )
    parser.add_argument(
        '--use-cache',
        action=arg_parsers.StoreTrueFalseAction,
        help='Whether to look for the result in the query cache.',
    )
    parser.add_argument(
        '--use-legacy-sql',
        action=arg_parsers.StoreTrueFalseAction,
        help="Whether to use BigQuery's legacy SQL dialect for this query.",
    )

  def Run(self, args):
    """Executes the BigQuery SQL query.

    Args:
      args: The parsed command-line arguments.

    Returns:
      The created Job resource when --async is specified, or a generator of
      formatted row dicts (via StreamQueryResult) when running synchronously.
      Calliope's Display() pipeline formats and prints the returned object
      using either the default/user-specified --format or the dynamically
      registered table(...) format for query results.

    Raises:
      core_exceptions.Error: If the query fails to execute.
    """
    query = args.sql_query
    if not query:
      query = console_io.ReadFromFileOrStdin('-', binary=False)
    query_utils.ValidateQuery(query)
    query_utils.ValidateQueryFlags(
        is_async=args.async_,
        job_id=args.job_id,
        job_creation_mode=args.job_creation_mode,
    )

    project = args.project or properties.VALUES.core.project.Get(required=True)
    client = api_util.GetApiClient(location=args.location)
    messages = client.MESSAGES_MODULE

    if args.job_id:
      insert_request = query_utils.CreateJobInsertRequest(
          query=query,
          project=project,
          job_id=args.job_id,
          use_cache=args.use_cache,
          use_legacy_sql=args.use_legacy_sql,
          location=args.location,
      )
      job = client.jobs.Insert(insert_request)
      if args.async_:
        # Calliope's Display() prints the returned Job resource using the
        # default resource format (YAML) or the user-specified --format flag.
        return job

      if job.status and job.status.errorResult:
        raise core_exceptions.Error(
            job.status.errorResult.message or 'Query execution failed.'
        )
      query_result = query_utils.WaitForQueryResults(
          client, project, job.jobReference
      )
    else:
      # Default query mode (jobs.query)
      query_request = query_utils.CreateQueryRequest(
          query=query,
          job_creation_mode=args.job_creation_mode,
          use_cache=args.use_cache,
          use_legacy_sql=args.use_legacy_sql,
          location=args.location,
      )
      request = messages.BigqueryJobsQueryRequest(
          projectId=project,
          queryRequest=query_request,
      )
      query_result = client.jobs.Query(request)
      if not query_result.jobComplete:
        query_result = query_utils.WaitForQueryResults(
            client,
            project,
            query_result.jobReference,
        )

    if query_result.errors:
      raise core_exceptions.Error(
          query_result.errors[0].message or 'Query execution failed.'
      )

    schema = query_result.schema
    if schema and hasattr(schema, 'fields') and schema.fields:
      cols = [f.name for f in schema.fields]
      if not args.IsSpecified('format') and cols:
        args.GetDisplayInfo().AddFormat('table({0})'.format(','.join(cols)))

    # Calliope's resource printer consumes this generator and renders the rows
    # using the table(...) format registered above (or the user's --format).
    return query_utils.StreamQueryResult(client, project, query_result, schema)
