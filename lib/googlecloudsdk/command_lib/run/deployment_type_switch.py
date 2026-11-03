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
"""Config changes that clean up stale state when switching deployment types.

A container can be deployed from an image, a legacy (Cloud Build) source build,
a unified (server-side Cloud Run) source build, or a no-build / local-build
source deployment. Each deployment type persists its own annotations and
container fields on the service; switching a container from one type to another
must clear the state left behind by the previous type.
"""

from typing import Any, Dict

from googlecloudsdk.api_lib.run import service as service_lib
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import validators


def GetDeploymentTypeSwitchChanges(
    service: Any,
    containers: Dict[str, Any],
    enable_unified_build: bool = False,
) -> list[config_changes.ConfigChanger]:
  """Generates deletion changers to clean up stale annotations.

  Args:
    service: The existing service being updated, or None for a new service.
    containers: The container args being deployed, keyed by container name. An
      empty name targets the ingress container (--container not used).
    enable_unified_build: Whether unified build is enabled. Clearing a
      container's stale build config applies in every track; the remaining
      cleanup only applies when unified build is enabled.

  Returns:
    The config changes to apply before the deployment's own changes. Empty
    unless an existing service is being updated.
  """
  if not service:
    return []

  changes = []
  for name, container_args in containers.items():
    changes.extend(
        _GetContainerDeploymentTypeSwitchChanges(
            service, name, container_args, enable_unified_build
        )
    )
  return changes


def _GetContainerDeploymentTypeSwitchChanges(
    service: Any,
    name: str,
    container_args: Any,
    enable_unified_build: bool = False,
) -> list[config_changes.ConfigChanger]:
  """Generates switch changes for a container."""
  # Empty name (--container flag not used) targets the ingress container.
  ingress_name = service.template.container.name or ''
  name = name or ingress_name
  is_ingress = name == ingress_name

  is_image = (
      not getattr(container_args, 'source', None)
      and getattr(container_args, 'image', None) is not None
  )
  is_source_build = validators.IsSourceBuild(container_args)
  is_legacy_build = is_source_build and not enable_unified_build
  is_unified_build = is_source_build and enable_unified_build

  changes = []

  # 1. Clear container build_config (only used by Unified Build). Applies in
  # all release tracks: unified build is Alpha only, so a deploy in any other
  # track is always a switch away from it and must not carry the stale build
  # config forward.
  if not is_unified_build:
    changes.append(
        config_changes.ContainerBuildConfigChange(
            container_name=name or None, build_config=None
        )
    )

  # The remaining cleanup is Alpha only.
  if enable_unified_build:
    # 2. Clear template sources (only used by Unified, No-Build, Local-Build).
    if is_image or is_legacy_build:
      changes.append(config_changes.SourcesAnnotationChange(deletes=[name]))

    # 3. Clear template base_images (unless --base-image is explicitly set).
    if is_image and not flags.FlagIsExplicitlySet(container_args, 'base_image'):
      changes.append(config_changes.BaseImagesAnnotationChange(deletes=[name]))

    # 4. Clear service-level legacy build annotations if the ingress container
    # is not built from source. Source builds own them: a legacy build re-sets
    # them, and with unified build enabled, the annotations left by a previous
    # legacy build are converted into the container's build config and deleted
    # by the unified build change rather than here.
    if is_ingress and not is_source_build:
      changes.extend(
          config_changes.DeleteAnnotationChange(key)
          for key in service_lib.RUN_FUNCTIONS_BUILD_ANNOTATIONS
      )

  return changes
