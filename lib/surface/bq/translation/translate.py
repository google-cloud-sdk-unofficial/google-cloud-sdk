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
"""Implements command to translate a SQL query."""

import functools
import json
import os
import typing

from apitools.base.py import encoding
from googlecloudsdk.api_lib.bq import util as api_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bq import command_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


@functools.cache
def _get_dialect_map():
  """Gets a mapping from lower-cased dialect names to their canonical names.

  The mapping is loaded from a JSON resource file.

  Returns:
    A dict mapping lower-cased dialect names (or legacy batch names) to their
    canonical names.

  Raises:
    exceptions.Error: If the dialect registry fails to load.
  """
  try:
    file_path = os.path.join(os.path.dirname(__file__), 'dialect_registry.json')
    registry = json.loads(files.ReadFileContents(file_path))
    dialect_map = {}
    for dialect in registry.get('input_dialects', []):
      legacy_name = dialect.get('legacy_batch_name')
      name = dialect.get('name')
      if legacy_name:
        dialect_map[legacy_name.lower()] = legacy_name
      elif name:
        dialect_map[name.lower()] = name
    return dialect_map
  except Exception as e:
    raise exceptions.Error(f'Failed to load dialect registry: {e}')


def _get_task_type(source_dialect: str) -> str:
  """Returns the migration task type based on the source dialect."""
  dialect_map = _get_dialect_map()
  mapped_dialect = dialect_map.get(
      source_dialect.lower(), source_dialect.capitalize()
  )
  return f'{mapped_dialect}2BigQuery_Translation'


def _build_translation_details(messages, query):
  """Builds the translation details message for the migration task."""
  translation_details = (
      messages.GoogleCloudBigqueryMigrationV2TranslationDetails(
          targetReturnLiterals=['sql/query.sql'],
          targetTypes=['sql'],
      )
  )

  literal_mapping = messages.GoogleCloudBigqueryMigrationV2SourceTargetMapping(
      sourceSpec=messages.GoogleCloudBigqueryMigrationV2SourceSpec(
          literal=messages.GoogleCloudBigqueryMigrationV2Literal(
              literalString=query, relativePath='query.sql'
          )
      )
  )
  translation_details.sourceTargetMapping = [literal_mapping]

  return translation_details


def _build_migration_workflow(messages, query, source_dialect):
  """Builds the migration workflow message and returns it with the task type."""
  task_type = _get_task_type(source_dialect)
  translation_details = _build_translation_details(messages, query)

  task = messages.GoogleCloudBigqueryMigrationV2MigrationTask(
      type=task_type, translationDetails=translation_details
  )

  workflow_tasks_value = messages.GoogleCloudBigqueryMigrationV2MigrationWorkflow.TasksValue(
      additionalProperties=[
          messages.GoogleCloudBigqueryMigrationV2MigrationWorkflow.TasksValue.AdditionalProperty(
              key='translation_task', value=task
          )
      ]
  )
  workflow = messages.GoogleCloudBigqueryMigrationV2MigrationWorkflow(
      tasks=workflow_tasks_value
  )
  return workflow, task_type


def _parse_task_result(wait_response):
  """Parses the workflow wait response into component task details."""
  translated_sql = None
  result_task = None
  console_uri = ''
  report_log_messages = []

  if wait_response.tasks and wait_response.tasks.additionalProperties:
    result_task = wait_response.tasks.additionalProperties[0].value
    if result_task.taskResult and result_task.taskResult.translationTaskResult:
      literals = result_task.taskResult.translationTaskResult.translatedLiterals
      for literal in literals:
        if literal.relativePath == 'sql/query.sql':
          translated_sql = literal.literalString
          break
      console_uri = result_task.taskResult.translationTaskResult.consoleUri
      report_log_messages = (
          result_task.taskResult.translationTaskResult.reportLogMessages
      )

  return result_task, translated_sql, console_uri, report_log_messages


def _format_log_result(
    wait_response, task_type, result_task, console_uri, report_log_messages
):
  """Formats the log result dictionary from the task components."""
  result = {
      'name': wait_response.name,
      'type': task_type,
      'state': wait_response.state.name if wait_response.state else '',
      'consoleUri': console_uri,
      'reportLogMessages': (
          [encoding.MessageToDict(msg) for msg in report_log_messages]
          if report_log_messages
          else []
      ),
  }

  if result_task:
    if result_task.processingError:
      result['processingError'] = encoding.MessageToDict(
          result_task.processingError
      )
    if result_task.resourceErrorDetails:
      result['resourceErrorDetails'] = [
          encoding.MessageToDict(msg)
          for msg in result_task.resourceErrorDetails
      ]

  return result


def _handle_task_failure(wait_response, result_task):
  """Checks the task state for failure and raises an exception if needed."""
  if result_task and result_task.state and result_task.state.name == 'FAILED':
    log.error('Workflow wait_response: %s', wait_response)
    if result_task.processingError:
      log.error('Task processing error: %s', result_task.processingError)
      error_details = []
      if (
          hasattr(result_task.processingError, 'message')
          and result_task.processingError.message
      ):
        error_details.append(result_task.processingError.message)
      if (
          hasattr(result_task.processingError, 'reason')
          and result_task.processingError.reason
      ):
        error_details.append(result_task.processingError.reason)
      error_str = ' '.join(error_details) if error_details else 'Unknown error'
      log.err.Print(f'Task processing error: {error_str}')
    if result_task.resourceErrorDetails:
      log.error('Task resource errors: %s', result_task.resourceErrorDetails)
    raise exceptions.Error('Failed to retrieve the translated SQL query.')


def _process_workflow_result(wait_response, task_type, args):
  """Processes the completed workflow and handles output/logging."""
  result_task, translated_sql, console_uri, report_log_messages = (
      _parse_task_result(wait_response)
  )

  result = _format_log_result(
      wait_response, task_type, result_task, console_uri, report_log_messages
  )

  if args.translation_log_file:
    files.WriteFileContents(args.translation_log_file, yaml.dump(result))
    log.status.Print(
        f'Successfully saved translation logs to {args.translation_log_file}.'
    )

  _handle_task_failure(wait_response, result_task)

  if not translated_sql:
    raise exceptions.Error('Failed to retrieve the translated SQL query.')

  if args.output_file and args.output_file != '-':
    files.WriteFileContents(args.output_file, translated_sql)
    log.status.Print(
        f'Successfully translated and saved to {args.output_file}.'
    )
  else:
    log.out.Print('Translated query:')
    log.out.Print(translated_sql)

  if args.translation_log_file:
    # Return None to avoid duplicating output in standard terminal output.
    return None

  log.out.Print('\nTranslation logs:')
  return result


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Translate(base.Command):
  """Translate a SQL query from a source dialect to BigQuery."""

  detailed_help = {
      'brief': 'Translate a SQL query from a source dialect to BigQuery.',
      'DESCRIPTION': """\
Translate a SQL query from a source dialect to BigQuery.

The command reads a SQL query from standard input (or an input file) and
prints the translated query to standard output (or an output file).
""",
      'EXAMPLES': """\
To translate a Snowflake query from stdin, run:

  $ echo 'SELECT * FROM test.my_table;' | {command} --source-dialect=SNOWFLAKE --location=us

To translate a Snowflake query from a file and save the output and logs to files, run:

  $ {command} \\
      --source-dialect=SNOWFLAKE \\
      --location=us \\
      --project=my-project \\
      --input-file=input.sql \\
      --output-file=output.sql \\
      --translation-log-file=translation_logs.yaml
""",
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--source-dialect',
        help='Source dialect of the query.',
        required=True,
    )
    parser.add_argument(
        '--location',
        help='Google Cloud Storage location to use for the translation.',
        required=True,
    )
    parser.add_argument(
        '--output-file',
        help=(
            'File to which to write the translated SQL. Writes to stdout if'
            " not provided or if set to ``-''."
        ),
        required=False,
    )
    parser.add_argument(
        '--input-file',
        help=(
            'File from which to read the SQL query to translate. Can be piped'
            ' through stdin as well.'
        ),
        required=False,
    )
    parser.add_argument(
        '--translation-log-file',
        help='File to which to write the translation logs.',
        required=False,
    )

  def Run(self, args):
    query = console_io.ReadFromFileOrStdin(args.input_file or '-', binary=False)

    if not query:
      raise exceptions.Error('No input query provided.')

    client = api_util.GetMigrationApiClient()
    client.additional_http_headers[api_util.TOOL_TAG_HEADER] = (
        api_util.GCLOUD_TOOL_TAG
    )
    messages = typing.cast(
        typing.Any, apis.GetMessagesModule('bigquerymigration', 'v2')
    )
    migration_service = client.projects_locations_workflows

    project = args.project or properties.VALUES.core.project.Get(required=True)
    location = args.location

    workflow, task_type = _build_migration_workflow(
        messages, query, args.source_dialect
    )

    request_type = api_util.GetMigrationApiMessage(
        'BigquerymigrationProjectsLocationsWorkflowsCreateRequest'
    )
    request = request_type(
        parent=f'projects/{project}/locations/{location}',
        googleCloudBigqueryMigrationV2MigrationWorkflow=workflow,
    )

    response = migration_service.Create(request)

    workflow_ref = resources.REGISTRY.ParseRelativeName(
        response.name,
        collection='bigquerymigration.projects.locations.workflows',
    )
    poller = command_utils.BqMigrationWorkflowPoller(migration_service)

    wait_response = waiter.WaitFor(
        poller=poller,
        operation_ref=workflow_ref,
        message='Running translation workflow [{}]'.format(response.name),
    )

    return _process_workflow_result(wait_response, task_type, args)
