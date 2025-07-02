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

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.run import artifact_registry
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import up
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


DEFAULT_REPO_NAME = 'cloud-run-source-deploy'


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
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
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    flags.AddDeployFromComposeArgument(parser)
    flags.AddRegionArg(parser)
    flags.AddDebugFlag(parser)
    flags.AddDryRunFlag(parser)

  @staticmethod
  def Args(parser):
    Up.CommonArgs(parser)

  def Run(self, args):
    """Deploy a container from the source Compose file to Cloud Run."""
    region = flags.GetRegion(args, prompt=True)
    self._SetRegionConfig(region)
    repo = self._GenerateRepositoryName(
        properties.VALUES.core.project.Get(required=True),
        region,
    )
    docker_repo = docker_util.DockerRepo(
        project_id=properties.VALUES.core.project.Get(required=True),
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
    response = command_executor(
        repo=repo,
        compose_file=compose_file,
        debug=args.debug,
        dry_run=args.dry_run,
    )
    return self._DefaultOperationResponseHandler(response)

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
          'Default region set to {region}.You can change the region with gcloud'
          ' config set run/region {region}.\n'.format(region=region)
      )
      properties.VALUES.run.region.Set(region)

  def _GetComposeFile(self):
    if os.path.exists('compose.yaml'):
      return 'compose.yaml'
    else:
      raise exceptions.ConfigurationError(
          'No compose file found. Please provide a compose file.'
      )

  def _CreateARRepository(self, docker_repo):
    """Create an Artifact Registry Repository if not present."""
    pretty_print.Success(
        f'Creating AR Repository in the region: {docker_repo.location}'
    )
    artifact_registry.CreateRepository(docker_repo, skip_activation_prompt=True)
