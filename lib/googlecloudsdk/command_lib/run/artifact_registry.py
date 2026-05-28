# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for working with Artifact Registry repositories."""

import re

from apitools.base.py import exceptions as base_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.artifacts import requests
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io

_AR_IMAGE_URI_REGEX = r'([\w-]+)-docker\.pkg\.dev/([\w-]+)/([\w-]+)'
_AR_LENIENT_IMAGE_URI_REGEX = r'^[^/]+/([\w-]+)/([\w-]+)/([\w-]+)'


def _RegionFromZone(zone):
  return '-'.join(zone.split('-')[:2])


def RepoRegion(args, cluster_location=None):
  """Returns the region for the Artifact Registry repo.

   The intended behavior is platform-specific:
   * managed: Same region as the service (run/region or --region). For
     multi-region services, we will use the first specified region.
   * gke: Appropriate region based on cluster zone (cluster_location arg)
   * kubernetes: The run/region config value will be used or an exception
     raised when unset.

  Args:
    args: Namespace, the args namespace.
    cluster_location: The zone which a Cloud Run for Anthos cluster resides.
      When specified, this will result in the region for this zone being
      returned.

  Returns:
    The appropriate region for the repository.
  """
  if cluster_location:
    return _RegionFromZone(cluster_location)
  first_region = flags.GetFirstRegion(args)
  if first_region:
    return first_region
  region = flags.GetRegion(args, prompt=False)
  if region:
    return region

  raise exceptions.ArgumentError(
      'To deploy from source with this platform, you must set run/region via '
      '"gcloud config set run/region REGION".'
  )


def ShouldCreateRepository(
    repo, skip_activation_prompt=False, skip_console_prompt=False
):
  """Checks for the existence of the provided repository.

  If the provided repository does not exist, the user will be prompted
  as to whether they would like to continue.

  Args:
    repo: googlecloudsdk.command_lib.artifacts.docker_util.DockerRepo defining
      the repository.
    skip_activation_prompt: bool determining if the client should prompt if the
      API isn't activated.
    skip_console_prompt: bool determining if the client should prompt the user
      if the repository doesn't exist.

  Returns:
    A boolean indicating whether a repository needs to be created.
  """
  try:
    requests.GetRepository(
        repo.GetRepositoryName(),
        skip_activation_prompt,
        location=repo.location,
    )
    return False
  except base_exceptions.HttpForbiddenError:
    log.error(
        'Permission denied while accessing Artifact Registry. Artifact '
        'Registry access is required to deploy from source.'
    )
    raise
  except base_exceptions.HttpBadRequestError:
    log.error('Error in retrieving repository from Artifact Registry.')
    raise
  except base_exceptions.HttpNotFoundError:
    if skip_console_prompt:
      return True
    message = (
        'Deploying from source requires an Artifact Registry Docker '
        'repository to store built containers. A repository named '
        '[{name}] in region [{location}] will be created.'.format(
            name=repo.repo, location=repo.location
        )
    )

    console_io.PromptContinue(message, cancel_on_no=True)

  return True


def CreateRepository(repo, skip_activation_prompt=False):
  """Creates an Artifact Registry repostiory and waits for the operation.

  Args:
    repo: googlecloudsdk.command_lib.artifacts.docker_util.DockerRepo defining
      the repository to be created.
    skip_activation_prompt: True if
  """
  messages = requests.GetMessages()
  repository_message = messages.Repository(
      name=repo.GetRepositoryName(),
      description='Cloud Run Source Deployments',
      format=messages.Repository.FormatValueValuesEnum.DOCKER,
  )

  op = requests.CreateRepository(
      repo.project, repo.location, repository_message, skip_activation_prompt
  )
  op_resource = resources.REGISTRY.ParseRelativeName(
      op.name, collection='artifactregistry.projects.locations.operations'
  )

  client = requests.GetClient(location=repo.location)
  waiter.WaitFor(
      waiter.CloudOperationPoller(
          client.projects_locations_repositories,
          client.projects_locations_operations,
      ),
      op_resource,
  )


def ValidateAndGetArRepository(
    annotated_build_image_uri, already_activated_services
):
  """Checks the format and existence of the repository in Artifact Registry."""
  is_default_universe = properties.IsDefaultUniverse()

  # 1. Primary Check: Standard GDU format with regional existence validation
  match = re.match(_AR_IMAGE_URI_REGEX, annotated_build_image_uri)

  if match:
    region = match.group(1)
    project_id = match.group(2)
    repo_id = match.group(3)
    ar_repo = docker_util.DockerRepo(
        project_id=project_id,
        location_id=region,
        repo_id=repo_id,
    )
    # Raise an error if the repo doesn't exist, will not attempt to create it.
    if ShouldCreateRepository(
        ar_repo,
        skip_activation_prompt=already_activated_services,
        skip_console_prompt=True,
    ):
      raise c_exceptions.InvalidArgumentException(
          '--image',
          'The artifact repository provided does not exist: '
          f'{annotated_build_image_uri}.'
          ' Please create the repository and try again.',
      )
    return ar_repo.GetDockerString()

  # 2. Fallback Check: Lenient structural validation for custom/future domains
  # Matches a hostname followed by exactly three path segments (e.g.
  # prefix/project/repo)
  # Only apply this fallback in non-default universes.
  if not is_default_universe:
    match = re.match(_AR_LENIENT_IMAGE_URI_REGEX, annotated_build_image_uri)
    if match:
      return match.group(0)

  # 3. Neither matched, raise standard format error
  raise c_exceptions.InvalidArgumentException(
      '--image',
      'The artifact repository found for the function '
      'was not in the expected format '
      '[REGION]-docker.pkg.dev/[PROJECT-ID]/[REPO-NAME] or\n'
      '[REGION]-docker.pkg.dev/[PROJECT-ID]/[REPO-NAME]/[SERVICE-NAME],'
      ' please try again. \n'
      f'Retrieved value was: {annotated_build_image_uri}',
  )

