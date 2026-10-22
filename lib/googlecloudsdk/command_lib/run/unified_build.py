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
"""Utilities for configuring unified source builds in `gcloud run deploy`."""

from collections.abc import Mapping
import copy
import json
import logging
import os
import re
from typing import Any

from apitools.base.py import encoding
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import service as service_lib
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.run import artifact_registry
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import validators
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.generated_clients.apis.run.v2 import run_v2_messages

_GPU_BUILD_MACHINE_TYPE = 'E2_HIGHCPU_8'

_BuildConfiguration = run_v2_messages.GoogleCloudRunV2BuildConfiguration
_BuildpacksBuild = (
    run_v2_messages.GoogleCloudRunV2BuildConfigurationBuildpacksBuild
)
_DockerBuild = run_v2_messages.GoogleCloudRunV2BuildConfigurationDockerBuild
_WorkerConfiguration = run_v2_messages.GoogleCloudRunV2WorkerConfiguration
_CloudBuildWorkerConfiguration = (
    run_v2_messages.GoogleCloudRunV2CloudBuildWorkerConfiguration
)


def GetUnifiedBuildChanges(
    service: service_lib.Service | None,
    container_args: Any,
    skip_activation_prompt: bool = False,
    service_ref: Any = None,
) -> list[config_changes.ConfigChanger]:
  """Configures a source container for unified build and returns its changes.
  """
  container_name = container_args.local_context.name or None
  container_key = container_name or ''
  changes = []

  # 1. Load previous build config and source URI (rolling forward legacy
  # service-level build-* annotations, only for the ingress build container).
  if _ShouldRollForwardLegacyAnnotations(service, container_args):
    build_config = _GetLegacyBuildConfig(service.annotations)
    source_uri = service.source_location
    changes.extend(
        config_changes.DeleteAnnotationChange(key)
        for key in service_lib.RUN_FUNCTIONS_BUILD_ANNOTATIONS
        if key in service.annotations
    )
  else:
    build_config = _GetExistingBuildConfig(service, container_name)
    source_uri = _GetSourceUriFromSourcesAnnotation(service, container_key)

  # 2. Configure source, validate image repo, apply flags to build config.
  match = re.search(r'gs://([^/]+)/.*', source_uri or '')
  # Like legacy build, source is None if pattern doesn't match.
  container_args.local_context.source_bucket = (
      match.group(1) if match else None
  )
  image_repository_uri = None
  if getattr(container_args, 'image', None):
    repository = artifact_registry.ValidateAndGetArRepository(
        container_args.image, skip_activation_prompt, enable_by_default=True
    )
    validators.ValidateServiceNameFromImage(
        container_args.image, service_ref.servicesId
    )
    image_repository_uri = f'{repository}/{service_ref.servicesId}'
  container_args.image = ''
  build_config = _ApplyFlagsToBuildConfig(
      container_args, service, build_config, image_repository_uri
  )

  # 3. Emit container command, ABIU base-images, and build_config changes.
  # Remove previously set command for function builds.
  if build_config.buildpacksBuild and getattr(container_args, 'function', None):
    changes.append(
        config_changes.ContainerCommandChange([], container_name=container_name)
    )
  # ABIU is default on unless specified otherwise.
  changes.append(
      _GetBaseImagesAnnotationChange(
          container_args, container_key, build_config
      )
  )
  changes.append(
      config_changes.ContainerBuildConfigChange(
          container_name=container_name, build_config=build_config
      )
  )
  return changes


def _ApplyFlagsToBuildConfig(
    container_args: parser_extensions.Namespace,
    service: service_lib.Service | None,
    config: _BuildConfiguration,
    image_repository_uri: str | None = None,
) -> _BuildConfiguration:
  """Merges a container's build flags on top of `config`."""
  if image_repository_uri:
    config.imageRepositoryUri = image_repository_uri
  config.serviceAccount = _ApplyFlag(
      container_args, 'build_service_account', config.serviceAccount
  )

  if os.path.exists(os.path.join(container_args.source, 'Dockerfile')):
    config.dockerBuild = _DockerBuild()
    config.buildpacksBuild = None
  else:
    config.dockerBuild = None
    buildpacks = config.buildpacksBuild or _BuildpacksBuild()
    buildpacks.buildBaseImageUri = _ApplyFlag(
        container_args, 'base_image', buildpacks.buildBaseImageUri
    )
    buildpacks.environmentVariables = _ApplyBuildEnvVars(
        container_args, buildpacks.environmentVariables
    )
    config.buildpacksBuild = buildpacks

  config.workerConfiguration = _ApplyWorkerConfiguration(
      container_args, service, config.workerConfiguration
  )
  return config


def _GetBuildMachineType(
    container_args: Any, service: service_lib.Service | None
) -> str | None:
  """Gets the default pool build machine type to use based on user flags and annotations."""
  gpu_type = getattr(container_args, 'gpu_type', None)
  gpu_count = getattr(container_args, 'gpu', None)
  if gpu_count == '0':
    return None
  if gpu_type is not None or gpu_count is not None:
    return _GPU_BUILD_MACHINE_TYPE
  if service and service.template.node_selector.get(
      k8s_object.GPU_TYPE_NODE_SELECTOR
  ):
    return _GPU_BUILD_MACHINE_TYPE
  return None


def _ApplyFlag(
    container_args: parser_extensions.Namespace, dest: str, current: Any
) -> Any:
  """Returns the value of a build setting after applying its flags."""
  if container_args.IsKnownAndSpecified('clear_' + dest):
    return None
  if container_args.IsKnownAndSpecified(dest):
    return getattr(container_args, dest)
  return current


def _ApplyBuildEnvVars(
    container_args: parser_extensions.Namespace,
    current: _BuildpacksBuild.EnvironmentVariablesValue | None,
) -> _BuildpacksBuild.EnvironmentVariablesValue | None:
  """Returns the buildpacks env vars after applying build-env-vars and --function."""
  env_vars = dict(
      map_util.ApplyMapFlags(
          {p.key: p.value for p in current.additionalProperties}
          if current
          else {},
          **map_util.GetMapFlagsFromArgs('build-env-vars', container_args),
      )
  )
  function = getattr(container_args, 'function', None)
  if function:
    env_vars['GOOGLE_FUNCTION_TARGET'] = function
  if not env_vars:
    return None
  return encoding.DictToAdditionalPropertyMessage(
      env_vars, _BuildpacksBuild.EnvironmentVariablesValue
  )


def _ApplyWorkerConfiguration(
    container_args: parser_extensions.Namespace,
    service: service_lib.Service | None,
    current: _WorkerConfiguration | None,
) -> _WorkerConfiguration | None:
  """Returns the worker configuration after applying worker pool and GPU flags."""
  current_pool = (
      current.cloudBuildWorkerConfiguration.workerPool
      if current and current.cloudBuildWorkerConfiguration
      else None
  )
  worker_pool = _ApplyFlag(container_args, 'build_worker_pool', current_pool)
  machine_type = _GetBuildMachineType(container_args, service)
  if not worker_pool and not machine_type:
    return None
  return _WorkerConfiguration(
      cloudBuildWorkerConfiguration=_CloudBuildWorkerConfiguration(
          workerPool=worker_pool, machineType=machine_type
      )
  )


def _ShouldRollForwardLegacyAnnotations(
    service: service_lib.Service | None,
    container_args: Any,
) -> bool:
  """Returns whether the container is an ingress build rolling forward legacy annotations."""
  if not service:
    return False
  is_ingress = (container_args.local_context.name or '') == (
      service.template.container.name or ''
  )
  has_existing_build_config = bool(service.template.container.build_config)
  is_source_build = validators.IsSourceBuild(container_args)
  has_legacy_annotations = any(
      k in service.annotations
      for k in service_lib.RUN_FUNCTIONS_BUILD_ANNOTATIONS
  )
  return (
      is_ingress
      and not has_existing_build_config
      and is_source_build
      and has_legacy_annotations
  )


def _GetLegacyBuildConfig(
    annotations: Mapping[str, str],
) -> _BuildConfiguration:
  """Creates an initial BuildConfiguration from legacy `build-*` annotations."""
  env_vars = json.loads(
      annotations.get(service_lib.RUN_FUNCTIONS_BUILD_ENV_VARS_ANNOTATION, '{}')
  )
  function_target = annotations.get(
      service_lib.RUN_FUNCTIONS_BUILD_FUNCTION_TARGET_ANNOTATION
  )
  if function_target:
    env_vars['GOOGLE_FUNCTION_TARGET'] = function_target

  return _BuildConfiguration(
      serviceAccount=annotations.get(
          service_lib.RUN_FUNCTIONS_BUILD_SERVICE_ACCOUNT_ANNOTATION
      ),
      buildpacksBuild=_BuildpacksBuild(
          buildBaseImageUri=annotations.get(
              service_lib.RUN_FUNCTIONS_BUILD_BASE_IMAGE
          ),
          environmentVariables=encoding.DictToAdditionalPropertyMessage(
              env_vars, _BuildpacksBuild.EnvironmentVariablesValue
          ),
      ),
      workerConfiguration=_WorkerConfiguration(
          cloudBuildWorkerConfiguration=_CloudBuildWorkerConfiguration(
              workerPool=annotations.get(
                  service_lib.RUN_FUNCTIONS_BUILD_WORKER_POOL_ANNOTATION
              )
          )
      ),
  )


def _GetExistingBuildConfig(
    service: service_lib.Service | None, container_name: str | None
) -> _BuildConfiguration:
  """Returns a copy of the container's existing build_config, or a new one."""
  if not service:
    return _BuildConfiguration()
  container = (
      service.template.containers.get(container_name)
      if container_name
      else service.template.container
  )
  if container and container.build_config:
    return copy.deepcopy(container.build_config)
  return _BuildConfiguration()


def _GetSourceUriFromSourcesAnnotation(
    service: service_lib.Service | None, container_key: str
) -> str | None:
  """Returns `container_key`'s source URI from `run.googleapis.com/sources`."""
  if not service or not service.source_deploy_source_location_map:
    return None
  try:
    sources = json.loads(service.source_deploy_source_location_map)
  except (json.JSONDecodeError, TypeError) as e:
    logging.debug('failed to parse source location: %s', e)
    return None
  return sources.get(container_key) if isinstance(sources, dict) else None


def _GetBaseImagesAnnotationChange(
    container_args: parser_extensions.Namespace,
    container_key: str,
    build_config: _BuildConfiguration,
) -> config_changes.BaseImagesAnnotationChange:
  """Returns the ABIU `run.googleapis.com/base-images` annotation change."""
  base_image = (
      build_config.buildpacksBuild.buildBaseImageUri
      if build_config.buildpacksBuild
      else None
  )
  enable_automatic_updates = (
      bool(container_args.automatic_updates)
      if container_args.IsKnownAndSpecified('automatic_updates')
      else True
  )
  if base_image and enable_automatic_updates:
    return config_changes.BaseImagesAnnotationChange(
        updates={container_key: base_image}
    )
  return config_changes.BaseImagesAnnotationChange(deletes=[container_key])
