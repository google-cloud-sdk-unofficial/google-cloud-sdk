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
"""Command for deploying containers from Compose file to Cloud Run."""

import os

from googlecloudsdk.api_lib.run import api_enabler
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.run import artifact_registry
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import up
from googlecloudsdk.command_lib.run.compose import compose_resource
from googlecloudsdk.command_lib.run.compose import exceptions as compose_exceptions
from googlecloudsdk.command_lib.run.compose import exit_codes
from googlecloudsdk.command_lib.run.compose import tracker as stages
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker


DEFAULT_REPO_NAME = 'cloud-run-source-deploy'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Up(base.BinaryBackedCommand):
  """Deploy to Cloud Run from compose specification."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To deploy a container from the source Compose file on Cloud Run:

              $ {command} compose.yaml

          To deploy to Cloud Run with unauthenticated access:

              $ {command} compose.yaml --allow-unauthenticated
         """,
  }

  @staticmethod
  def CommonArgs(parser):
    flags.AddDeployFromComposeArgument(parser)
    flags.AddRegionArg(parser)
    flags.AddDryRunFlag(parser)
    flags.AddAllowUnauthenticatedFlag(parser)
    parser.add_argument(
        '--no-build',
        action='store_true',
        help='Skip building from source if applicable.',
    )

  @staticmethod
  def Args(parser):
    Up.CommonArgs(parser)

  def _ResourceAndTranslateRun(
      self, command_executor, compose_file, repo, project_number, region, args
  ):
    """Handles the resource and translate run logic."""
    release_track = self.ReleaseTrack()
    cfg_dir = config.Paths().global_config_dir
    # We construct out_dir within the gcloud config directory to avoid
    # polluting the user's source codebase with generated files.
    # cfg_dir ensures the path is platform-specific.
    out_dir = os.path.join(cfg_dir, 'surface', 'run', 'compose')
    resource_response = command_executor(
        command='resource',
        compose_file=compose_file,
        debug=log.GetVerbosity() <= log.logging.DEBUG,
        dry_run=args.dry_run,
        region=region,
        out=out_dir,
    )
    error_message = 'Failed to process compose file.'
    if not resource_response.stdout:
      # This should never happen since project is always returned by resource
      # command
      if resource_response.stderr and isinstance(
          resource_response.stderr, list
      ):
        error_message = resource_response.stderr[-1]
      metrics.CustomKeyValue(
          properties.VALUES.metrics.command_name.Get(),
          'resource_error',
          error_message,
      )
      raise compose_exceptions.GoBinaryError(
          error_message, resource_response.exit_code
      )
    try:
      config_obj = compose_resource.ResourcesConfig.from_json(
          resource_response.stdout[0]
      )
      log.debug('Successfully parsed resources config proto.')
      log.debug(f'ResourcesConfig:\n{config_obj}')

      if not config_obj.project:
      # TODO: b/474246517 - Fix error message type.
        raise compose_exceptions.GcloudError(
            'Could not determine project name from compose file.',
            exit_code=exit_codes.PROJECT_NAME_MISSING,
        )

      project_id = properties.VALUES.core.project.Get(required=True)
      required_apis = config_obj.get_required_apis(args.no_build)
      if required_apis:
        api_enabler.check_and_enable_apis(project_id, required_apis)

      with progress_tracker.StagedProgressTracker(
          'Setting up resources...',
          self._AddTrackerStages(config_obj),
          failure_message='Setup failed',
          suppress_output=False,
          success_message='Resource setup complete.',
      ) as tracker:
        resources_config = config_obj.handle_resources(
            region, repo, tracker, args.no_build
        )
        log.debug('Handled ResourcesConfig:\n%s', resources_config)

      # Serialize the handled config to JSON
      resources_config_json = resources_config.to_json()
      response = command_executor(
          command='translate',
          repo=repo,
          compose_file=compose_file,
          resources_config=resources_config_json,  # Pass the JSON string
          debug=log.GetVerbosity() <= log.logging.DEBUG,
          dry_run=args.dry_run,
          project_number=project_number,
          region=region,
          out=out_dir,
      )

      if response.stdout:
        translate_result = compose_resource.TranslateResult.from_json(
            response.stdout[0]
        )
        log.debug('Successfully translated resources config to YAML.')
        log.debug(
            'YAML files:\n'
            f'{list(translate_result.services.values()) + list(translate_result.models.values())}'
        )
        for model_yaml in translate_result.models.values():
          compose_resource.deploy_application(
              yaml_file_path=model_yaml,
              region=region,
              args=args,
              release_track=release_track,
          )
        for service_yaml in translate_result.services.values():
          compose_resource.deploy_application(
              yaml_file_path=service_yaml,
              region=region,
              args=args,
              release_track=release_track,
          )
      else:
        if response.stderr and isinstance(response.stderr, list):
          error_message = response.stderr[-1]
        metrics.CustomKeyValue(
            properties.VALUES.metrics.command_name.Get(),
            'translate_error',
            error_message,
        )
        raise compose_exceptions.GoBinaryError(
            error_message, response.exit_code
        )

      return response
    except Exception as e:
      log.debug(f'Raw output: {resource_response.stdout}')
      raise compose_exceptions.GcloudError(
          str(e), exit_codes.UNKNOWN_ERROR
      ) from e

  def Run(self, args):
    """Deploy a container from the source Compose file to Cloud Run."""
    log.status.Print('Deploying from Compose to Cloud Run...')
    try:
      region = flags.GetRegion(args, prompt=True)
    except properties.RequiredPropertyError as e:
      raise compose_exceptions.GcloudError(
          str(e), exit_codes.REGION_NOT_SET
      )
    self._SetRegionConfig(region)
    try:
      project = properties.VALUES.core.project.Get(required=True)
    except properties.RequiredPropertyError as e:
      raise compose_exceptions.GcloudError(
          str(e), exit_codes.PROJECT_NOT_SET
      )
    project_number = projects_util.GetProjectNumber(project)
    repo = self._GenerateRepositoryName(
        project,
        region,
    )
    docker_repo = docker_util.DockerRepo(
        project_id=project,
        location_id=region,
        repo_id=DEFAULT_REPO_NAME,
    )

    if artifact_registry.ShouldCreateRepository(
        docker_repo, skip_activation_prompt=True, skip_console_prompt=True
    ):
      self._CreateARRepository(docker_repo)

    command_executor = up.RunComposeWrapper()
    if args.compose_file:
      compose_file = args.compose_file
    else:
      compose_file = self._GetComposeFile()

    response = self._ResourceAndTranslateRun(
        command_executor, compose_file, repo, project_number, region, args
    )
    return response

  def _GenerateRepositoryName(self, project, region):
    """Generate a name for the repository."""
    repository = '{}-docker.pkg.dev'.format(region)
    return '{}/{}/{}'.format(
        repository, project.replace(':', '/'), DEFAULT_REPO_NAME
    )

  def _SetRegionConfig(self, region):
    """Set the region config."""
    if not properties.VALUES.run.region.Get():
      log.status.Print(
          'Region set to {region}.You can change the region with gcloud'
          ' config set run/region {region}.\n'.format(region=region)
      )
      properties.VALUES.run.region.Set(region)

  def _GetComposeFile(self):
    for filename in [
        'compose.yaml',
        'compose.yml',
        'docker-compose.yaml',
        'docker-compose.yml',
    ]:
      if os.path.exists(filename):
        return filename
    raise exceptions.ConfigurationError(
        'No compose file found. Please provide a compose file.',
        exit_code=exit_codes.COMPOSE_FILE_NOT_FOUND,
    )

  def _CreateARRepository(self, docker_repo):
    """Create an Artifact Registry Repository if not present."""
    pretty_print.Success(
        f'Creating AR Repository in the region: {docker_repo.location}'
    )
    artifact_registry.CreateRepository(docker_repo, skip_activation_prompt=True)

  def _AddTrackerStages(self, cfg):
    """Add a tracker to the progress tracker."""
    staged_operations = []
    if cfg.source_builds:
      for container_name in cfg.source_builds:
        staged_operations.append(
            progress_tracker.Stage(
                f'Building container {container_name} from source...',
                key=stages.StagedProgressTrackerStage.BUILD.get_key(
                    container=container_name
                ),
            )
        )
    if cfg.secrets:
      staged_operations.append(
          progress_tracker.Stage(
              'Creating secrets...',
              key=stages.StagedProgressTrackerStage.SECRETS.get_key(),
          )
      )
    if cfg.volumes.bind_mount or cfg.volumes.named_volume:
      staged_operations.append(
          progress_tracker.Stage(
              'Creating volumes...',
              key=stages.StagedProgressTrackerStage.VOLUMES.get_key(),
          )
      )
    if cfg.configs:
      staged_operations.append(
          progress_tracker.Stage(
              'Creating configs...',
              key=stages.StagedProgressTrackerStage.CONFIGS.get_key(),
          )
      )
    return staged_operations
