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
"""BigQuery query utility functions for gcloud alpha bq query."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.bq import util as api_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.bq import command_utils
from googlecloudsdk.core import exceptions as core_exceptions

DEFAULT_QUERY_TIMEOUT_MS = 3000


def ValidateQuery(query):
  """Validates that a query string is not empty or whitespace only."""
  if not query or not query.strip():
    raise exceptions.RequiredArgumentException(
        'SQL_QUERY',
        'Query must be specified on the command line or passed on stdin.',
    )


def ValidateQueryFlags(is_async=False, job_id=None, job_creation_mode=None):
  """Validates flag combinations for the bq query command."""
  if is_async and not job_id:
    raise exceptions.InvalidArgumentException(
        '--async',
        'Running query asynchronously is only supported when --job-id is'
        ' specified.',
    )
  if job_id and job_creation_mode == 'JOB_CREATION_OPTIONAL':
    raise exceptions.InvalidArgumentException(
        '--job-id',
        '--job-id forces a job to be created and is incompatible with'
        ' --job-creation-mode=JOB_CREATION_OPTIONAL.',
    )


class BqQueryResultsPoller(waiter.OperationPoller):
  """Poller that waits for query completion via jobs.GetQueryResults."""

  def __init__(self, jobs_service):
    self.jobs_service = jobs_service

  def IsDone(self, response):
    """Returns True when the query job has completed."""
    return bool(response.jobComplete)

  def Poll(self, poll_request):
    """Calls jobs.GetQueryResults (long-polls up to 10s on the server)."""
    return self.jobs_service.GetQueryResults(poll_request)

  def GetResult(self, response):
    """Returns the completed GetQueryResultsResponse directly."""
    return response


def WaitForQueryResults(client, project, job_ref):
  """Polls jobs.GetQueryResults using waiter until jobComplete is True.

  Args:
    client: BigQuery API client.
    project: str, Fallback GCP project ID.
    job_ref: JobReference message from a Job or QueryResponse.

  Returns:
    Completed GetQueryResultsResponse message.
  """
  if not job_ref or not job_ref.jobId:
    raise core_exceptions.Error(
        'Query did not complete and no job reference was returned.'
    )
  messages = client.MESSAGES_MODULE
  poll_request = messages.BigqueryJobsGetQueryResultsRequest(
      jobId=job_ref.jobId,
      projectId=job_ref.projectId or project,
      location=job_ref.location,
      maxResults=command_utils.DEFAULT_MAX_QUERY_RESULTS,
  )
  poller = BqQueryResultsPoller(client.jobs)
  # jobs.GetQueryResults is a server-side long-polling RPC that blocks on the
  # BigQuery backend for up to 10 seconds per request by default, so no
  # additional client-side sleep is needed between polling requests.
  return waiter.WaitFor(
      poller=poller,
      operation_ref=poll_request,
      message='Waiting for query to complete',
      pre_start_sleep_ms=0,
      sleep_ms=0,
      jitter_ms=0,
  )


def StreamQueryResult(client, project, query_result, schema):
  """Streams formatted rows from a QueryResponse or GetQueryResultsResponse."""
  messages = client.MESSAGES_MODULE
  if query_result.rows:
    for row in FormatRows(schema, query_result.rows):
      yield row

  page_token = query_result.pageToken
  job_ref = query_result.jobReference
  if job_ref and page_token:
    while page_token:
      page_request = messages.BigqueryJobsGetQueryResultsRequest(
          jobId=job_ref.jobId,
          projectId=job_ref.projectId or project,
          location=job_ref.location,
          pageToken=page_token,
      )
      page_response = client.jobs.GetQueryResults(page_request)
      if page_response.rows:
        for row in FormatRows(schema, page_response.rows):
          yield row
      page_token = page_response.pageToken


def CreateQueryRequest(
    query,
    job_creation_mode=None,
    use_cache=None,
    use_legacy_sql=None,
    location=None,
):
  """Creates a QueryRequest message for the jobs.query API.

  Args:
    query: str, SQL query to execute.
    job_creation_mode: str, Optional job creation mode enum value.
    use_cache: bool or None, Whether to use query cache.
    use_legacy_sql: bool or None, Whether to use legacy SQL.
    location: str or None, The geographic location where the job should run.

  Returns:
    QueryRequest message.
  """
  messages = api_util.GetApiMessages()
  query_request = messages.QueryRequest(
      query=query,
      timeoutMs=DEFAULT_QUERY_TIMEOUT_MS,
  )
  if job_creation_mode is not None:
    query_request.jobCreationMode = (
        messages.QueryRequest.JobCreationModeValueValuesEnum(job_creation_mode)
    )
  if use_cache is not None:
    query_request.useQueryCache = use_cache
  if use_legacy_sql is not None:
    query_request.useLegacySql = use_legacy_sql
  if location is not None:
    query_request.location = location
  return query_request


def CreateJobInsertRequest(
    query,
    project,
    job_id=None,
    use_cache=None,
    use_legacy_sql=None,
    location=None,
):
  """Creates a BigqueryJobsInsertRequest message for jobs.insert API.

  Args:
    query: str, SQL query to execute.
    project: str, GCP project ID.
    job_id: str or None, Custom job ID to use for the query job.
    use_cache: bool or None, Whether to use query cache.
    use_legacy_sql: bool or None, Whether to use legacy SQL.
    location: str or None, The geographic location where the job should run.

  Returns:
    BigqueryJobsInsertRequest message.
  """
  messages = api_util.GetApiMessages()
  job_config_query = messages.JobConfigurationQuery(query=query)
  if use_cache is not None:
    job_config_query.useQueryCache = use_cache
  if use_legacy_sql is not None:
    job_config_query.useLegacySql = use_legacy_sql

  job_ref = messages.JobReference(projectId=project)
  if job_id is not None:
    job_ref.jobId = job_id
  if location is not None:
    job_ref.location = location

  job = messages.Job(
      configuration=messages.JobConfiguration(query=job_config_query),
      jobReference=job_ref,
  )
  return messages.BigqueryJobsInsertRequest(job=job, projectId=project)


def FormatRows(schema, rows):
  """Converts API TableRows and TableSchema into dictionaries.

  Args:
    schema: TableSchema message or dict containing field metadata.
    rows: list of TableRow messages or dicts.

  Yields:
    dict of {column_name: cell_value} for each row.
  """
  if not rows:
    return
  if hasattr(schema, 'fields'):
    schema_dict = encoding.MessageToPyValue(schema)
  else:
    schema_dict = schema or {}
  fields = schema_dict.get('fields', [])
  for row in rows:
    if hasattr(row, 'f'):
      row_dict = encoding.MessageToPyValue(row)
    else:
      row_dict = row or {}
    yield FormatRow(fields, row_dict)


def FormatRow(fields, row_dict):
  """Formats a single row into a dictionary of {column_name: value}.

  Args:
    fields: list of dicts representing field metadata.
    row_dict: dict containing row representation with 'f' key.

  Returns:
    dict mapping column names to parsed values.
  """
  if not row_dict or not fields:
    return {}
  cells = row_dict.get('f', [])
  result = {}
  for field, cell in zip(fields, cells):
    name = field.get('name')
    val = _ConvertCellValue(
        field, cell.get('v') if isinstance(cell, dict) else None
    )
    result[name] = val
  return result


def _ConvertCellValue(field, v):
  """Recursively converts a cell value based on field type and mode."""
  if v is None:
    return None
  field_type = field.get('type', '').upper()
  mode = field.get('mode', 'NULLABLE').upper()
  subfields = field.get('fields', [])

  if field_type == 'RECORD':
    if mode == 'REPEATED':
      if isinstance(v, list):
        return [
            FormatRow(subfields, sub_item.get('v', {}))
            if isinstance(sub_item, dict)
            else sub_item
            for sub_item in v
        ]
      return []
    else:
      if isinstance(v, dict):
        return FormatRow(subfields, v)
      return v
  elif mode == 'REPEATED':
    if isinstance(v, list):
      return [
          sub_item.get('v') if isinstance(sub_item, dict) else sub_item
          for sub_item in v
      ]
    return []
  else:
    return v
