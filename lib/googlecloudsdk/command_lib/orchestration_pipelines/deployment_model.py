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
"""Orchestration Pipelines deployment model."""

from __future__ import annotations

from collections.abc import Mapping
import dataclasses
import re
from typing import Any, Literal


def _camel_to_snake(name):
  name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower()


@dataclasses.dataclass
class ResourceProfileModel:
  """Model for resourceProfile resource."""
  type: Literal['resourceProfile']
  path: str
  name: str | None = None
  names: list[str] | None = None


@dataclasses.dataclass
class MetadataModel:
  """Model for resource metadata."""

  # Applicable to: BigQuery Data Transfer Configs
  service_account_name: str | None = None

  # Applicable to: All (Global Override)
  location: str | None = None


@dataclasses.dataclass
class ResourceModel:
  """Generalized model for ordinary resources."""
  type: str
  name: str
  parent: str | None = None
  api_version: str | None = None
  definition: dict[str, Any] = dataclasses.field(default_factory=dict)
  metadata: MetadataModel = dataclasses.field(default_factory=MetadataModel)
  update_action: Literal['patch', 'skip', 'recreate'] = 'patch'


AnyResource = ResourceProfileModel | ResourceModel


@dataclasses.dataclass
class ArtifactStorageModel:
  """Model for artifact_storage."""

  bucket: str
  path_prefix: str


@dataclasses.dataclass
class PipelineModel:
  """Model for pipeline entry."""

  source: str


@dataclasses.dataclass
class EnvironmentModel:
  """Model for environment."""
  project: str
  region: str
  resources: list[AnyResource]
  composer_environment: str | None = None
  artifact_storage: ArtifactStorageModel | None = None
  pipelines: list[PipelineModel] | None = None
  variables: dict[str, str] | None = None
  secrets: dict[str, str] = dataclasses.field(default_factory=dict)


def _build_metadata(
    metadata_def: Mapping[str, Any] | None,
) -> MetadataModel:
  if not metadata_def:
    return MetadataModel()
  return MetadataModel(
      service_account_name=metadata_def.get('serviceAccountName'),
      location=metadata_def.get('location'),
  )


def build_resource(resource_def: Mapping[str, Any]) -> AnyResource:
  """Builds a resource model from its raw YAML definition."""
  resource_type = resource_def.get('type')
  if not resource_type:
    raise ValueError('Resource definition missing type')
  if resource_type == 'resourceProfile':
    return ResourceProfileModel(
        type=resource_type,
        name=resource_def.get('name'),
        names=resource_def.get('names'),
        path=resource_def.get('path'),
    )

  # For all other resources, use the generalized ResourceModel
  # Keep original casing for definition fields, but extract known top-level ones
  return ResourceModel(
      type=resource_type,
      name=resource_def.get('name'),
      definition=resource_def.get('definition', {}),
      parent=resource_def.get('parent'),
      api_version=resource_def.get('apiVersion'),
      metadata=_build_metadata(resource_def.get('metadata')),
      update_action=resource_def.get('updateAction', 'patch'),
  )


def _build_artifact_storage(
    storage_def: Mapping[str, Any] | None,
) -> ArtifactStorageModel | None:
  """Builds ArtifactStorageModel, handling None input gracefully."""
  if not storage_def:
    return None
  return ArtifactStorageModel(**storage_def)


def _build_environment(env_def: Mapping[str, Any]) -> EnvironmentModel:
  raw_resources = env_def.get('resources', [])
  if isinstance(raw_resources, dict):
    raw_resources = [raw_resources]

  resources = [build_resource(r) for r in raw_resources]
  artifact_storage = _build_artifact_storage(env_def.get('artifact_storage'))
  raw_pipelines = env_def.get('pipelines', [])
  pipelines = (
      [PipelineModel(**p) for p in raw_pipelines] if raw_pipelines else None
  )
  return EnvironmentModel(
      project=env_def['project'],
      region=env_def['region'],
      composer_environment=env_def.get('composer_environment'),
      resources=resources,
      artifact_storage=artifact_storage,
      pipelines=pipelines,
      variables=env_def.get('variables'),
      secrets=env_def.get('secrets') or {},
  )


@dataclasses.dataclass
class DeploymentModel:
  """Model for deployment file."""
  environments: dict[str, EnvironmentModel]

  @classmethod
  def build(cls, definition: Mapping[str, Any]) -> 'DeploymentModel':
    environments = {
        name: _build_environment(env_def)
        for name, env_def in definition.get('environments', {}).items()
    }
    return DeploymentModel(environments=environments)
