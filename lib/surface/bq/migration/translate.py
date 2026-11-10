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

import os
import typing

from apitools.base.py import encoding
from googlecloudsdk.api_lib.bq import util as api_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bq import command_utils
from googlecloudsdk.command_lib.bq.migration import translation_utils as utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import files

_DEFAULT_QUERY_RELATIVE_PATH = 'query.sql'
_TRANSLATED_SQL_RELATIVE_PATH = f'sql/{_DEFAULT_QUERY_RELATIVE_PATH}'
_SOURCE_SQL_SUGGESTION_RELATIVE_PATH = (
    f'source_sql_query_customization_suggestion/{_DEFAULT_QUERY_RELATIVE_PATH}'
)
_TARGET_SQL_SUGGESTION_RELATIVE_PATH = (
    f'target_sql_query_customization_suggestion/{_DEFAULT_QUERY_RELATIVE_PATH}'
)
_EXPLANATION_RELATIVE_PATH = (
    f'translation_explanation_suggestion/{_DEFAULT_QUERY_RELATIVE_PATH}'
)
_GENERATED_DDL_RELATIVE_PATH = 'source_sql_metadata_generation_suggestion/'


def _build_translation_details(
    messages,
    query,
    explanation_output_file=None,
    translation_config_files=None,
    metadata_gcs_uri=None,
    source_ddl_output_file=None,
    source_sql_suggestion_output_file=None,
    target_sql_suggestion_output_file=None,
):
  """Builds the translation details message for the translation task."""
  target_return_literals = [_TRANSLATED_SQL_RELATIVE_PATH]
  target_types = ['sql']

  source_target_mapping = [
      messages.GoogleCloudBigqueryMigrationV2SourceTargetMapping(
          sourceSpec=messages.GoogleCloudBigqueryMigrationV2SourceSpec(
              literal=messages.GoogleCloudBigqueryMigrationV2Literal(
                  literalString=query,
                  relativePath=_DEFAULT_QUERY_RELATIVE_PATH,
              )
          )
      )
  ]

  if source_ddl_output_file:
    target_return_literals.append(_GENERATED_DDL_RELATIVE_PATH)
    if 'suggestion' not in target_types:
      target_types.append('suggestion')

  if source_sql_suggestion_output_file:
    if _SOURCE_SQL_SUGGESTION_RELATIVE_PATH not in target_return_literals:
      target_return_literals.append(_SOURCE_SQL_SUGGESTION_RELATIVE_PATH)
    if 'suggestion' not in target_types:
      target_types.append('suggestion')

  if target_sql_suggestion_output_file:
    if _TARGET_SQL_SUGGESTION_RELATIVE_PATH not in target_return_literals:
      target_return_literals.append(_TARGET_SQL_SUGGESTION_RELATIVE_PATH)
    if 'suggestion' not in target_types:
      target_types.append('suggestion')

  if explanation_output_file:
    target_return_literals.append(_EXPLANATION_RELATIVE_PATH)
    if 'suggestion' not in target_types:
      target_types.append('suggestion')
    ai_config = (
        'translation_rules:\n  - suggestion_type: "TRANSLATION_EXPLANATION"'
    )
    source_target_mapping.append(
        messages.GoogleCloudBigqueryMigrationV2SourceTargetMapping(
            sourceSpec=messages.GoogleCloudBigqueryMigrationV2SourceSpec(
                literal=messages.GoogleCloudBigqueryMigrationV2Literal(
                    literalString=ai_config,
                    relativePath='gcloud_default_inline.ai_config.yaml',
                )
            )
        )
    )

  if translation_config_files:
    for config_file in translation_config_files:
      filename = os.path.basename(config_file)
      if not (
          filename.endswith('.config.yaml')
          or filename.endswith('.ai_config.yaml')
      ):
        raise exceptions.Error(
            f'Translation config file "{config_file}" must end with'
            ' ".config.yaml" or ".ai_config.yaml".'
        )
      if filename.endswith('.ai_config.yaml'):
        if 'suggestion' not in target_types:
          target_types.append('suggestion')
        if _SOURCE_SQL_SUGGESTION_RELATIVE_PATH not in target_return_literals:
          target_return_literals.append(_SOURCE_SQL_SUGGESTION_RELATIVE_PATH)
        if _TARGET_SQL_SUGGESTION_RELATIVE_PATH not in target_return_literals:
          target_return_literals.append(_TARGET_SQL_SUGGESTION_RELATIVE_PATH)
      content = files.ReadFileContents(config_file)
      source_target_mapping.append(
          messages.GoogleCloudBigqueryMigrationV2SourceTargetMapping(
              sourceSpec=messages.GoogleCloudBigqueryMigrationV2SourceSpec(
                  literal=messages.GoogleCloudBigqueryMigrationV2Literal(
                      literalString=content,
                      relativePath=filename,
                  )
              )
          )
      )

  if metadata_gcs_uri:
    source_target_mapping.append(
        messages.GoogleCloudBigqueryMigrationV2SourceTargetMapping(
            sourceSpec=messages.GoogleCloudBigqueryMigrationV2SourceSpec(
                gcsFilePath=metadata_gcs_uri
            )
        )
    )

  return messages.GoogleCloudBigqueryMigrationV2TranslationDetails(
      targetReturnLiterals=target_return_literals,
      targetTypes=target_types,
      sourceTargetMapping=source_target_mapping,
  )


def _build_migration_workflow(
    messages,
    query,
    source_dialect,
    target_dialect,
    explanation_output_file=None,
    translation_config_files=None,
    metadata_gcs_uri=None,
    source_ddl_output_file=None,
    source_sql_suggestion_output_file=None,
    target_sql_suggestion_output_file=None,
):
  """Builds the translation message and returns it with the task type."""
  task_type = utils.get_task_type(source_dialect, target_dialect)
  translation_details = _build_translation_details(
      messages,
      query,
      explanation_output_file,
      translation_config_files,
      metadata_gcs_uri,
      source_ddl_output_file,
      source_sql_suggestion_output_file,
      target_sql_suggestion_output_file,
  )

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
  """Parses the wait response into component task details."""
  translated_sql = None
  source_sql_suggestion = None
  target_sql_suggestion = None
  explanation = None
  generated_ddl = None
  result_task = None
  console_uri = ''
  report_log_messages = []

  if wait_response.tasks and wait_response.tasks.additionalProperties:
    translation_task_prop = next(
        (
            p
            for p in wait_response.tasks.additionalProperties
            if p.key == 'translation_task'
        ),
        None,
    )
    if translation_task_prop:
      result_task = translation_task_prop.value
    if (
        result_task
        and result_task.taskResult
        and result_task.taskResult.translationTaskResult
    ):
      literals = result_task.taskResult.translationTaskResult.translatedLiterals
      for literal in literals:
        if literal.relativePath == _TRANSLATED_SQL_RELATIVE_PATH:
          translated_sql = literal.literalString
        elif literal.relativePath == _SOURCE_SQL_SUGGESTION_RELATIVE_PATH:
          source_sql_suggestion = literal.literalString
        elif literal.relativePath == _TARGET_SQL_SUGGESTION_RELATIVE_PATH:
          target_sql_suggestion = literal.literalString
        elif literal.relativePath == _EXPLANATION_RELATIVE_PATH:
          explanation = literal.literalString
        elif literal.relativePath == _GENERATED_DDL_RELATIVE_PATH:
          generated_ddl = literal.literalString
      console_uri = result_task.taskResult.translationTaskResult.consoleUri
      report_log_messages = (
          result_task.taskResult.translationTaskResult.reportLogMessages
      )

  return (
      result_task,
      translated_sql,
      source_sql_suggestion,
      target_sql_suggestion,
      explanation,
      generated_ddl,
      console_uri,
      report_log_messages,
  )


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


def _handle_task_failure(wait_response, result_task) -> bool:
  """Logs task failure details and returns True if the task failed."""
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
    return True
  return False


def _process_workflow_result(wait_response, task_type, args):
  """Processes the completed translation and handles output/logging."""
  (
      result_task,
      translated_sql,
      source_sql_suggestion,
      target_sql_suggestion,
      explanation,
      generated_ddl,
      console_uri,
      report_log_messages,
  ) = _parse_task_result(wait_response)

  result = _format_log_result(
      wait_response, task_type, result_task, console_uri, report_log_messages
  )

  if args.translation_log_file:
    files.WriteFileContents(args.translation_log_file, yaml.dump(result))
    log.status.Print(
        f'Successfully saved translation logs to {args.translation_log_file}.'
    )

  task_failed = _handle_task_failure(wait_response, result_task)
  if task_failed or not translated_sql:
    if not args.translation_log_file:
      log.status.Print('\nTranslation logs:')
      resource_printer.Print(
          result,
          args.format or 'yaml',
          out=log.status,
          single=True,
      )
    raise exceptions.Error('Failed to retrieve the translated SQL query.')

  write_sql_to_file = bool(args.output_file and args.output_file != '-')
  printed_to_stdout = False

  if source_sql_suggestion:
    if args.source_sql_suggestion_output_file:
      files.WriteFileContents(
          args.source_sql_suggestion_output_file, source_sql_suggestion
      )
      log.status.Print(
          'Applied SOURCE_SQL AI rules to the input query and saved the'
          ' generated source SQL suggestion to'
          f' {args.source_sql_suggestion_output_file}.'
      )
    else:
      log.status.Print(
          'Applied SOURCE_SQL AI rules to the input query to generate the'
          ' source SQL suggestion (use --source-sql-suggestion-output-file'
          ' to save it to a file).'
      )
      log.out.Print(
          'Source SQL suggestion (generated by SOURCE_SQL AI rules and passed'
          ' to the translation engine):'
      )
      log.out.Print(source_sql_suggestion)
      printed_to_stdout = True
  elif args.source_sql_suggestion_output_file:
    log.warning(
        'No source SQL suggestion was generated; %s was not written. Ensure'
        ' an .ai_config.yaml file with SOURCE_SQL rules is provided via'
        ' --translation-config-files.',
        args.source_sql_suggestion_output_file,
    )

  if write_sql_to_file:
    files.WriteFileContents(args.output_file, translated_sql)
    if source_sql_suggestion:
      log.status.Print(
          'Processed the source SQL suggestion through the translation engine.'
          f' Successfully translated and saved to {args.output_file}.'
      )
    elif target_sql_suggestion:
      log.status.Print(
          'Processed the input query through the translation engine.'
          f' Successfully translated and saved to {args.output_file}.'
      )
    else:
      log.status.Print(
          f'Successfully translated and saved to {args.output_file}.'
      )
  else:
    if source_sql_suggestion:
      log.status.Print(
          'Processed the source SQL suggestion through the translation engine'
          ' to produce the translated SQL.'
      )
    elif target_sql_suggestion:
      log.status.Print(
          'Processed the input query through the translation engine to produce'
          ' the translated SQL.'
      )
    log.out.Print(
        '\nTranslated query:' if printed_to_stdout else 'Translated query:'
    )
    log.out.Print(translated_sql)
    printed_to_stdout = True

  if target_sql_suggestion:
    if args.target_sql_suggestion_output_file:
      files.WriteFileContents(
          args.target_sql_suggestion_output_file, target_sql_suggestion
      )
      log.status.Print(
          'Processed the engine-translated SQL with TARGET_SQL AI rules and'
          ' saved the generated target SQL suggestion to'
          f' {args.target_sql_suggestion_output_file}.'
      )
    else:
      log.status.Print(
          'Processed the engine-translated SQL with TARGET_SQL AI rules to'
          ' generate the target SQL suggestion (use'
          ' --target-sql-suggestion-output-file to save it to a file).'
      )
      target_header = (
          'Target SQL suggestion (generated by applying TARGET_SQL AI rules'
          ' to the translated SQL):'
      )
      log.out.Print(
          f'\n{target_header}' if printed_to_stdout else target_header
      )
      log.out.Print(target_sql_suggestion)
  elif args.target_sql_suggestion_output_file:
    log.warning(
        'No target SQL suggestion was generated; %s was not written. Ensure'
        ' an .ai_config.yaml file with TARGET_SQL rules is provided via'
        ' --translation-config-files.',
        args.target_sql_suggestion_output_file,
    )

  if args.explanation_output_file and explanation:
    files.WriteFileContents(args.explanation_output_file, explanation)
    log.status.Print(
        'Successfully saved translation explanation to'
        f' {args.explanation_output_file}.'
    )

  if args.source_ddl_output_file and generated_ddl:
    files.WriteFileContents(args.source_ddl_output_file, generated_ddl)
    log.status.Print(
        f'Successfully saved source DDL to {args.source_ddl_output_file}.'
    )

  if args.translation_log_file:
    # Return None to avoid duplicating output in standard terminal output.
    return None

  log.out.Print('\nTranslation logs:')
  return result


@base.RegionalEndpointsSupported
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Translate(base.Command):
  """Translate a SQL query from a source dialect to BigQuery."""

  detailed_help = {
      'brief': 'Translate a SQL query from a source dialect to BigQuery.',
      'DESCRIPTION': (
          """\
Translate a SQL query from a source dialect to BigQuery.

The command reads a SQL query from standard input (or an input file) and
prints the translated query to standard output (or an output file).
"""
      ),
      'EXAMPLES': (
          """\
To translate a Snowflake query from stdin, run:

  $ echo 'SELECT * FROM test.my_table;' | {command} --source-dialect=SNOWFLAKE --target-dialect=BIGQUERY --location=us

To translate a Snowflake query from a file and save the output and logs to files, run:

  $ {command} \\
      --source-dialect=SNOWFLAKE \\
      --target-dialect=BIGQUERY \\
      --location=us \\
      --project=my-project \\
      --input-file=input.sql \\
      --output-file=output.sql \\
      --translation-log-file=translation_logs.yaml
"""
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--source-dialect',
        help=(
            'Source dialect of the query. See supported dialects in'
            ' https://docs.cloud.google.com/bigquery/docs/enable-sql-translations#supported_sql_dialects'
        ),
        required=True,
    )
    parser.add_argument(
        '--target-dialect',
        help=(
            'Target dialect of the query. See supported dialects in'
            ' https://docs.cloud.google.com/bigquery/docs/enable-sql-translations#supported_sql_dialects'
        ),
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
    parser.add_argument(
        '--explanation-output-file',
        help='File to which to write the translation explanation.',
        required=False,
    )
    parser.add_argument(
        '--metadata-gcs-uri',
        help='Cloud Storage URI for the metadata zip file.',
        required=False,
    )
    parser.add_argument(
        '--translation-config-files',
        type=arg_parsers.ArgList(),
        metavar='CONFIG_FILE',
        help=(
            'A comma-separated list of paths to YAML configuration files. File'
            ' names must end with .config.yaml or .ai_config.yaml. See'
            ' https://docs.cloud.google.com/bigquery/docs/config-yaml-translation'
            ' for more details.'
        ),
        required=False,
    )
    parser.add_argument(
        '--source-ddl-output-file',
        help='File to which to write the generated source DDL.',
        required=False,
    )
    parser.add_argument(
        '--source-sql-suggestion-output-file',
        help=(
            'File to which to write the AI-customized source SQL generated by'
            ' SOURCE_SQL rules in an .ai_config.yaml file before the query is'
            ' processed by the translation engine. Writes to stdout if not'
            ' provided when a source SQL suggestion is generated.'
        ),
        required=False,
    )
    parser.add_argument(
        '--target-sql-suggestion-output-file',
        help=(
            'File to which to write the AI-customized target SQL generated by'
            ' applying TARGET_SQL rules in an .ai_config.yaml file to the'
            ' engine-translated SQL. Writes to stdout if not provided when a'
            ' target SQL suggestion is generated.'
        ),
        required=False,
    )

  def Run(self, args):
    query = console_io.ReadFromFileOrStdin(args.input_file or '-', binary=False)

    if not query:
      raise exceptions.Error('No input query provided.')

    project = args.project or properties.VALUES.core.project.Get(required=True)
    location = args.location

    client = api_util.GetMigrationApiClient(location=location)
    messages = typing.cast(
        typing.Any, apis.GetMessagesModule('bigquerymigration', 'v2')
    )
    migration_service = client.projects_locations_workflows

    workflow, task_type = _build_migration_workflow(
        messages,
        query,
        args.source_dialect,
        args.target_dialect,
        explanation_output_file=args.explanation_output_file,
        translation_config_files=args.translation_config_files,
        metadata_gcs_uri=args.metadata_gcs_uri,
        source_ddl_output_file=args.source_ddl_output_file,
        source_sql_suggestion_output_file=(
            args.source_sql_suggestion_output_file
        ),
        target_sql_suggestion_output_file=(
            args.target_sql_suggestion_output_file
        ),
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
        message='Running translation [{}]'.format(response.name),
    )

    return _process_workflow_result(wait_response, task_type, args)
