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
"""Command for tearing down resources created by gcloud run compose up."""

import os

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run.compose import cleanup
from googlecloudsdk.command_lib.run.compose import exceptions as compose_exceptions
from googlecloudsdk.command_lib.run.compose import exit_codes
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Down(base.Command):
  """Tear down resources created by gcloud run compose up."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          {description}
          """
      ),
      'EXAMPLES': (
          """\
          To tear down resources in the current directory:

              $ {command}

          To tear down resources using a specific compose file:

              $ {command} compose.yaml
          """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.AddDeployFromComposeArgument(parser)
    flags.AddRegionArg(parser)

  def Run(self, args):
    # 1. Resolve compose file
    compose_file = args.compose_file
    if not compose_file:
      fallbacks = [
          'compose.yaml',
          'docker-compose.yaml',
          'compose.yml',
          'docker-compose.yml',
      ]
      for fallback in fallbacks:
        if os.path.exists(fallback):
          compose_file = fallback
          break
      if not compose_file:
        raise compose_exceptions.GcloudError(
            'No compose file found. Please specify a compose file or run the'
            ' command in a directory containing one of: compose.yaml,'
            ' docker-compose.yaml, compose.yml, docker-compose.yml.',
            exit_code=exit_codes.COMPOSE_FILE_NOT_FOUND,
        )

    log.status.Print(f'Using compose file: {compose_file}')

    # 2. Resolve project name from compose file
    try:
      compose_content = yaml.load_path(compose_file)
    except Exception as e:
      raise compose_exceptions.GcloudError(
          f'Failed to read/parse compose file {compose_file}: {e}',
          exit_code=exit_codes.CONFIG_INVALID,
      )

    project_name = None
    if compose_content and isinstance(compose_content, dict):
      project_name = compose_content.get('name')

    if not project_name:
      # Fallback to directory name of the compose file
      abs_path = os.path.abspath(compose_file)
      dir_path = os.path.dirname(abs_path)
      project_name = os.path.basename(dir_path)

    if not project_name:
      raise compose_exceptions.GcloudError(
          'Failed to resolve project name from compose file or directory.',
          exit_code=exit_codes.PROJECT_NAME_MISSING,
      )

    log.status.Print(f'Resolved project name: {project_name}')

    # 3. Resolve region
    region = flags.GetRegion(args, prompt=True)
    if not region:
      raise compose_exceptions.GcloudError(
          'Region is required.',
          exit_code=exit_codes.REGION_NOT_SET,
      )
    log.status.Print(f'Using region: {region}')

    # 4. Initialize Teardown Orchestrator
    project_id = properties.VALUES.core.project.Get(required=True)
    conn_context = connection_context.GetConnectionContext(
        args,
        product=flags.Product.RUN,
        release_track=self.ReleaseTrack(),
    )

    teardown = cleanup.ComposeTeardown(
        project_name=project_name,
        region=region,
        project_id=project_id,
        conn_context=conn_context,
        release_track=self.ReleaseTrack(),
    )

    # Phase 1: Discovery
    log.status.Print(
        'Discovering resources for project: {}...'.format(project_name)
    )
    discovered, disabled_apis = teardown.Discover()

    has_resources = any(discovered.values())
    if not has_resources:
      log.status.Print('No resources found to delete.')
      return {
          'compose_file': compose_file,
          'project_name': project_name,
          'deleted_resources': discovered,
      }

    # Phase 2: Validation
    log.status.Print('\nThe following resources will be deleted:')
    if discovered.get('services'):
      for s in discovered['services']:
        log.status.Print(' - [Cloud Run Service] {}'.format(s))
    if discovered.get('secrets'):
      for s in discovered['secrets']:
        log.status.Print(' - [Secret Manager Secret] {}'.format(s))
    if discovered.get('bucket'):
      log.status.Print(
          ' - [Cloud Storage Bucket] {}'.format(discovered['bucket'])
      )

    # Print warnings for disabled APIs only if services were found
    if discovered.get('services'):
      if disabled_apis.get('secrets'):
        log.status.Print(
            '\n[Note] Secret Manager API is disabled in this project. Assuming'
            ' no secrets were deployed.'
        )
      if disabled_apis.get('bucket'):
        log.status.Print(
            '\n[Note] Cloud Storage API is disabled in this project. Assuming'
            ' no GCS volumes were deployed.'
        )

    # Prompt user
    if not console_io.PromptContinue(
        message='\nDo you want to continue',
        default=False,
    ):
      raise console_io.OperationCancelledError('Aborted by user.')

    # Phase 3: Execution
    teardown.Delete(discovered)

    return {
        'compose_file': compose_file,
        'project_name': project_name,
        'deleted_resources': discovered,
    }
