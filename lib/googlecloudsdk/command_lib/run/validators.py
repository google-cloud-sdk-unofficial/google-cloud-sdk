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
"""Functions for validating flags and configurations for Cloud Run commands."""

import re
from typing import Any, Mapping

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import local_build
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

_IMAGE_URI_REGEX = (
    r'(?P<region>[\w-]+)-docker\.pkg\.dev/(?P<project_id>[\w-]+)/'
    r'(?P<repo_name>[\w-]+)/(?P<service_name>[\w-]+)(?:/(.+))?$'
)


def _IsIngressContainer(container):
  """Returns True if the container is an ingress container."""
  return container.IsSpecified('port') or container.IsSpecified('use_http2')


def ValidateIngressContainer(containers):
  if len(containers) > 1:
    ingress_containers = [
        c for c in containers.values() if _IsIngressContainer(c)
    ]
    if len(ingress_containers) != 1:
      raise c_exceptions.InvalidArgumentException(
          '--container',
          'Exactly one container must specify --port or --use-http2',
      )


def ValidateContainerLimit(containers):
  if len(containers) > 10:
    raise c_exceptions.InvalidArgumentException(
        '--container', 'Services may include at most 10 containers'
    )


def ValidateNoAutomaticUpdatesForContainers(
    deploy_from_source, containers, release_track
):
  for name, container in containers.items():
    if container.IsSpecified('automatic_updates'):
      is_not_source = name not in deploy_from_source
      is_no_build = (
          release_track != base.ReleaseTrack.GA
          and container.IsSpecified('no_build')
      )
      if is_not_source or is_no_build:
        raise c_exceptions.InvalidArgumentException(
            '--automatic-updates',
            '--automatic-updates can only be specified in the container that'
            ' builds from source.',
        )


def ValidateImplicitSourceContainers(
    source_containers: Mapping[str, Any],
) -> None:
  """Validates containers implicitly using source."""
  # allows at most one container that implicitly uses source
  containers_has_no_source_or_image = [
      name
      for name, container in source_containers.items()
      if not flags.FlagIsExplicitlySet(container, 'source')
  ]
  if len(containers_has_no_source_or_image) > 1:
    raise exceptions.RequiredImageArgumentException(
        containers_has_no_source_or_image
    )

  # helper to prompt for source if not provided.
  for name, container in source_containers.items():
    if not flags.FlagIsExplicitlySet(container, 'source'):
      if console_io.CanPrompt():
        container.source = flags.PromptForDefaultSource(name)
      else:
        if name:
          message = (
              'Container {} requires a container image to deploy (e.g.'
              ' `gcr.io/cloudrun/hello:latest`) if no build source is'
              ' provided.'.format(name)
          )
        else:
          message = (
              'Requires a container image to deploy (e.g.'
              ' `gcr.io/cloudrun/hello:latest`) if no build source is'
              ' provided.'
          )
        raise c_exceptions.RequiredArgumentException(
            '--image',
            message,
        )

  # ensure no_build and local_build are not used together.
  for container in source_containers.values():
    if getattr(container, 'no_build', False) and getattr(
        container, 'local_build', False
    ):
      raise c_exceptions.ConflictingArgumentsException(
          '--no-build', '--local-build'
      )


def ValidateUnifiedBuildProperty(deploy_from_source, containers, release_track):
  if properties.VALUES.run.enable_unified_build.GetBool():
    if release_track != base.ReleaseTrack.ALPHA:
      raise exceptions.ConfigurationError(
          'The `enable_unified_build` property is only supported in the Alpha'
          ' release track.'
      )
    if len(containers) > 1:
      for _, container in deploy_from_source.items():
        if not _IsIngressContainer(container):
          raise c_exceptions.InvalidArgumentException(
              '--container',
              'Building sidecars from source is currently not supported when'
              ' using unified build.',
          )


def ValidateNoBuildFromSource(source_containers, release_track):
  """Extra validation for Zip deployments.

  This is a no-op for if the --no-build flag is not set.

  Args:
    source_containers: The map of source container name to container
      object.
    release_track: The release track of the command.
  """
  for _, container_args in source_containers.items():
    if not IsNoBuildFromSource(release_track, container_args):
      continue

    if not container_args.IsSpecified('base_image'):
      raise c_exceptions.InvalidArgumentException(
          '--no-build',
          'Source deployment must specify --base-image when skipping Cloud'
          ' Build.',
      )
    if (
        container_args.IsSpecified('image')
        and getattr(container_args, 'image') != 'scratch'
    ):
      raise c_exceptions.InvalidArgumentException(
          '--image',
          'Source deployment --image must be set to "scratch" when skipping'
          'Cloud Build.',
      )


def IsNoBuildFromSource(release_track, container_args):
  """Checks if this is a source deployment that should skip the Cloud Build step."""
  if release_track == base.ReleaseTrack.GA:
    return False

  return container_args.IsSpecified('no_build')


def IsLocalBuildFromSource(release_track, container_args):
  """Checks if this is a source deployment that should use local build."""
  if release_track != base.ReleaseTrack.ALPHA:
    return False

  return container_args.IsSpecified('local_build')


def GetValidLocalBuildSourceContainer(release_track, build_from_source):
  """Checks if this is a local build source deployment."""
  if release_track != base.ReleaseTrack.ALPHA:
    return None
  if not build_from_source:
    return None
  local_build_containers = [
      container
      for container in build_from_source.values()
      if flags.FlagIsExplicitlySet(container, 'local_build')
  ]

  if len(local_build_containers) > 1:
    raise c_exceptions.InvalidArgumentException(
        '--local-build',
        'At most one container can be built locally.',
    )

  if local_build_containers:
    if (
        local_build_containers[0].IsSpecified('image')
        and getattr(local_build_containers[0], 'image') != 'scratch'
    ):
      raise c_exceptions.InvalidArgumentException(
          '--image',
          'Source deployment --image must be set to "scratch" when skipping'
          'Cloud Build.',
      )
    local_build.ValidateLocalBuildSource(local_build_containers[0].source)
    return local_build_containers[0]

  return None


def ValidateServiceNameFromImage(image_uri, service_id):
  """Checks the service extracted from the image uri matches the service id."""
  match = re.match(_IMAGE_URI_REGEX, image_uri)
  if (
      match
      and match.group('service_name')
      and match.group('service_name') != service_id
  ):
    raise c_exceptions.InvalidArgumentException(
        '--image',
        'The service name found in the Artifact Registry repository path, '
        f'{image_uri}, does not match the service name, {service_id}.',
    )
