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
"""Implements command to translate a batch of SQL queries."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bq import translation_utils as utils
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class TranslateBatch(base.Command):
  """Translates a batch of SQL queries.

  ## EXAMPLES

  To translate a batch of Teradata queries in Cloud Storage in location
  `us-central1`, run:

    $ {command} --source-dialect=teradata --target-dialect=bigquery
    --location=us-central1 --source-gcs-uris=gs://my-bucket/queries/
    --target-gcs-path=gs://my-bucket/output/

  To upload queries from a local directory and translate them, run:

    $ {command} --source-dialect=teradata --target-dialect=bigquery
    --location=us-central1 --source-local-dirs=./queries=gs://my-bucket/queries/
    --target-gcs-path=gs://my-bucket/output/
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--source-dialect',
        required=True,
        help='The dialect of the source SQL files.',
    )
    parser.add_argument(
        '--target-dialect',
        required=True,
        help='The dialect of the target SQL files.',
    )
    parser.add_argument(
        '--location',
        required=True,
        help='The location to execute the migration workflow.',
    )

    parser.add_argument(
        '--source-gcs-uris',
        type=arg_parsers.ArgList(),
        metavar='URI',
        help=(
            'List of Cloud Storage URI prefixes containing multiple source SQL'
            ' files.'
        ),
    )
    parser.add_argument(
        '--source-gcs-files',
        type=arg_parsers.ArgList(),
        metavar='FILE_URI',
        help=(
            'List of Cloud Storage URIs pointing to individual source files or'
            ' additional files. Note: these files must not be located within'
            ' the directory specified by --source-gcs-uris, or an error will'
            ' occur.'
        ),
    )

    parser.add_argument(
        '--target-gcs-path',
        required=True,
        help=(
            'The Cloud Storage directory URI where the translated output will'
            ' be written.'
        ),
    )

    parser.add_argument(
        '--source-local-dirs',
        type=arg_parsers.ArgDict(),
        metavar='LOCAL_DIR=CLOUD_STORAGE_URI',
        help=(
            'Map of local directories to their corresponding Cloud Storage URIs'
            ' (e.g., local_dir=gs://bucket/path). The local directories will be'
            ' uploaded to the specified Cloud Storage URIs before translation,'
            ' and those Cloud Storage URIs will be automatically included in'
            ' the translation job.'
        ),
    )
    parser.add_argument(
        '--source-local-files',
        type=arg_parsers.ArgDict(),
        metavar='LOCAL_FILE=CLOUD_STORAGE_FILE_URI',
        help=(
            'Map of local files to their corresponding Cloud Storage URIs'
            ' (e.g., local_file=gs://bucket/path/file.sql). The local files'
            ' will be uploaded to the specified Cloud Storage URIs before'
            ' translation, and those Cloud Storage URIs will be automatically'
            ' included in the translation job.'
        ),
    )

    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        '--enable-ai-suggestion',
        action='store_true',
        help='Enable AI suggestion to improve translation quality.',
    )
    parser.add_argument(
        '--target-types',
        type=arg_parsers.ArgList(),
        metavar='TARGET_TYPE',
        help=(
            'List of output types to generate. Supported values include `sql`'
            ' to translate SQL files, and `metadata` to translate metadata ZIP'
            ' files into DDL statements and table mappings. Specify both to'
            ' translate SQL files and metadata ZIP files in a single job,'
            ' instead of running a separate `gcloud alpha bq translation'
            ' translate-metadata` command. Defaults to `sql`.'
        ),
    )

  def Run(self, args):
    utils.validate_target_gcs_path(args.target_gcs_path)
    gcs_uris, gcs_files = utils.validate_source_inputs_and_upload_local_files(
        source_gcs_uris=args.source_gcs_uris or [],
        source_gcs_files=args.source_gcs_files or [],
        source_local_dirs=args.source_local_dirs or {},
        source_local_files=args.source_local_files or {},
    )

    client = utils.get_migration_client(location=args.location)
    messages = client.MESSAGES_MODULE
    migration_service = client.projects_locations_workflows

    project = properties.VALUES.core.project.Get(required=True)
    location = args.location

    task_type = utils.get_task_type(args.source_dialect, args.target_dialect)
    source_target_mapping = utils.build_source_target_mappings(
        messages, gcs_uris, gcs_files
    )
    target_types = list(args.target_types) if args.target_types else ['sql']
    if args.enable_ai_suggestion:
      target_types.append('suggestion')
    # Collapse duplicates while preserving order, so that redundant requests
    # such as `--target-types=suggestion --enable-ai-suggestion` are sent once.
    target_types = list(dict.fromkeys(target_types))

    translation_details = utils.build_translation_details(
        messages, args.target_gcs_path, source_target_mapping, target_types
    )

    task = messages.GoogleCloudBigqueryMigrationV2MigrationTask(
        type=task_type, translationDetails=translation_details
    )
    workflow = utils.build_migration_workflow(
        messages, 'translation_task', task
    )

    parent_ref = resources.REGISTRY.Create(
        'bigquerymigration.projects.locations',
        projectsId=project,
        locationsId=location,
    )
    request = messages.BigquerymigrationProjectsLocationsWorkflowsCreateRequest(
        parent=parent_ref.RelativeName(),
        googleCloudBigqueryMigrationV2MigrationWorkflow=workflow,
    )

    return utils.execute_workflow(
        migration_service=migration_service,
        workflow_request=request,
        task_type=task_type,
        is_async=args.async_,
        location=location,
    )
