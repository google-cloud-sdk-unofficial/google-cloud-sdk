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
  name: str
  source: str


@dataclasses.dataclass
class DataprocClusterModel:
  """Model for dataproc.cluster resource."""
  type: Literal['dataproc.cluster']
  name: str
  definition: dict[str, Any]


@dataclasses.dataclass
class BqDataTransferConfigModel:
  """Model for bigquery.datatransfer.config resource."""
  type: Literal['bigquery.datatransfer.config']
  name: str
  display_name: str
  definition: dict[str, Any]
  service_account_name: str | None = None


@dataclasses.dataclass
class DataformRepositoryModel:
  """Model for dataform.repository resource."""
  type: Literal['dataform.repository']
  name: str
  definition: dict[str, Any] | None = None


@dataclasses.dataclass
class DataformReleaseConfigModel:
  """Model for dataform.repository.releaseConfig resource."""
  type: Literal['dataform.repository.releaseConfig']
  name: str
  repository_name: str
  definition: dict[str, Any]


@dataclasses.dataclass
class DataformWorkflowConfigModel:
  """Model for dataform.repository.workflowConfig resource."""
  type: Literal['dataform.repository.workflowConfig']
  name: str
  repository_name: str
  definition: dict[str, Any]


AnyResource = (
    ResourceProfileModel
    | DataprocClusterModel
    | BqDataTransferConfigModel
    | DataformRepositoryModel
    | DataformReleaseConfigModel
    | DataformWorkflowConfigModel
)


@dataclasses.dataclass
class ArtifactStorageModel:
  """Model for artifact_storage."""

  bucket: str
  path_prefix: str


@dataclasses.dataclass
class EnvironmentModel:
  """Model for environment."""
  project: str
  region: str
  resources: list[AnyResource]
  composer_environment: str | None = None
  artifact_storage: ArtifactStorageModel | None = None
  variables: dict[str, str] | None = None


RESOURCE_MAPPING = {
    'resourceProfile': ResourceProfileModel,
    'dataproc.cluster': DataprocClusterModel,
    'bigquery.datatransfer.config': BqDataTransferConfigModel,
    'dataform.repository': DataformRepositoryModel,
    'dataform.repository.releaseConfig': DataformReleaseConfigModel,
    'dataform.repository.workflowConfig': DataformWorkflowConfigModel,
}


def _build_resource(resource_def: Mapping[str, Any]) -> AnyResource:
  resource_type = resource_def.get('type')
  model = RESOURCE_MAPPING.get(resource_type)
  if not model:
    raise ValueError(f'Unknown resource type: {resource_type}')
  snake_case_def = {_camel_to_snake(k): v for k, v in resource_def.items()}
  return model(**snake_case_def)


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
  resources = [_build_resource(r) for r in raw_resources]
  artifact_storage = _build_artifact_storage(env_def.get('artifact_storage'))
  return EnvironmentModel(
      project=env_def['project'],
      region=env_def['region'],
      composer_environment=env_def.get('composer_environment'),
      resources=resources,
      artifact_storage=artifact_storage,
      variables=env_def.get('variables'),
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
