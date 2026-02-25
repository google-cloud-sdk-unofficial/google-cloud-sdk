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
"""Dataform resource handler."""

from typing import Any, Dict, List

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines import deployment_model
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base


class DataformBaseHandler(base.GcpResourceHandler):
  """Base class for Dataform resource handlers."""

  api_name = "dataform"
  api_version = "v1beta1"

  def _get_location_path(self):
    return f"projects/{self.environment.project}/locations/{self.environment.region}"


class DataformRepositoryHandler(DataformBaseHandler):
  """Handler for Dataform Repository resources."""
  resource: deployment_model.DataformRepositoryModel

  def get_local_definition(self) -> dict[str, Any]:
    return self.resource.definition or {}

  def wait_for_operation(self, operation: Any) -> tuple[Any, str]:
    return operation, self.resource.name

  def get_resource_id(self) -> str:
    return self.resource.name

  def get_create_method(self) -> Any:
    return self.client.projects_locations_repositories.Create

  def get_update_method(self) -> Any:
    return self.client.projects_locations_repositories.Patch

  def find_existing_resource(self) -> Any:
    name = f"{self._get_location_path()}/repositories/{self.get_resource_id()}"
    request = self.messages.DataformProjectsLocationsRepositoriesGetRequest(
        name=name
    )
    try:
      return self.client.projects_locations_repositories.Get(request)
    except apitools_exceptions.HttpNotFoundError:
      return None

  def build_create_request(self, definition: Dict[str, Any]) -> Any:
    repository_message = encoding.DictToMessage(
        definition, self.messages.Repository
    )
    return self.messages.DataformProjectsLocationsRepositoriesCreateRequest(
        parent=self._get_location_path(),
        repository=repository_message,
        repositoryId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: Any,
      definition: Dict[str, Any],
      changed_fields: List[str],
  ) -> Any:
    repository_message = encoding.DictToMessage(
        definition, self.messages.Repository
    )
    repository_message.name = existing_resource.name
    return self.messages.DataformProjectsLocationsRepositoriesPatchRequest(
        name=existing_resource.name,
        repository=repository_message,
        updateMask=",".join(changed_fields),
    )


class DataformReleaseConfigHandler(DataformBaseHandler):
  """Handler for Dataform ReleaseConfig resources."""
  resource: deployment_model.DataformReleaseConfigModel

  def _get_repo_path(self):
    return f"projects/{self.environment.project}/locations/{self.environment.region}/repositories/{self.resource.repository_name}"

  def get_resource_id(self) -> str:
    return self.resource.name

  def get_create_method(self) -> Any:
    return self.client.projects_locations_repositories_releaseConfigs.Create

  def get_update_method(self) -> Any:
    return self.client.projects_locations_repositories_releaseConfigs.Patch

  def find_existing_resource(self) -> Any:
    name = f"{self._get_repo_path()}/releaseConfigs/{self.get_resource_id()}"
    request = self.messages.DataformProjectsLocationsRepositoriesReleaseConfigsGetRequest(
        name=name
    )
    try:
      return self.client.projects_locations_repositories_releaseConfigs.Get(
          request
      )
    except apitools_exceptions.HttpNotFoundError:
      return None

  def build_create_request(self, definition: Dict[str, Any]) -> Any:
    release_config_message = encoding.DictToMessage(
        definition, self.messages.ReleaseConfig
    )
    return self.messages.DataformProjectsLocationsRepositoriesReleaseConfigsCreateRequest(
        parent=self._get_repo_path(),
        releaseConfig=release_config_message,
        releaseConfigId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: Any,
      definition: Dict[str, Any],
      changed_fields: List[str],
  ) -> Any:
    release_config_message = encoding.DictToMessage(
        definition, self.messages.ReleaseConfig
    )
    release_config_message.name = existing_resource.name
    return self.messages.DataformProjectsLocationsRepositoriesReleaseConfigsPatchRequest(
        name=existing_resource.name,
        releaseConfig=release_config_message,
        updateMask=",".join(changed_fields),
    )


class DataformWorkflowConfigHandler(DataformBaseHandler):
  """Handler for Dataform WorkflowConfig resources."""
  resource: deployment_model.DataformWorkflowConfigModel

  def _get_repo_path(self):
    return f"projects/{self.environment.project}/locations/{self.environment.region}/repositories/{self.resource.repository_name}"

  def get_resource_id(self) -> str:
    return self.resource.name

  def get_create_method(self) -> Any:
    return self.client.projects_locations_repositories_workflowConfigs.Create

  def get_update_method(self) -> Any:
    return self.client.projects_locations_repositories_workflowConfigs.Patch

  def find_existing_resource(self) -> Any:
    name = f"{self._get_repo_path()}/workflowConfigs/{self.get_resource_id()}"
    request = self.messages.DataformProjectsLocationsRepositoriesWorkflowConfigsGetRequest(
        name=name
    )
    try:
      return self.client.projects_locations_repositories_workflowConfigs.Get(
          request
      )
    except apitools_exceptions.HttpNotFoundError:
      return None

  def get_local_definition(self) -> Dict[str, Any]:
    definition = super().get_local_definition()
    if ("releaseConfig" in definition and
        "/" not in definition["releaseConfig"]):
      definition["releaseConfig"] = (
          f"{self._get_repo_path()}/releaseConfigs/{definition['releaseConfig']}"
      )
    return definition

  def build_create_request(self, definition: Dict[str, Any]) -> Any:
    workflow_config_message = encoding.DictToMessage(
        definition, self.messages.WorkflowConfig
    )
    return self.messages.DataformProjectsLocationsRepositoriesWorkflowConfigsCreateRequest(
        parent=self._get_repo_path(),
        workflowConfig=workflow_config_message,
        workflowConfigId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: Any,
      definition: Dict[str, Any],
      changed_fields: List[str],
  ) -> Any:
    workflow_config_message = encoding.DictToMessage(
        definition, self.messages.WorkflowConfig
    )
    workflow_config_message.name = existing_resource.name
    return self.messages.DataformProjectsLocationsRepositoriesWorkflowConfigsPatchRequest(
        name=existing_resource.name,
        workflowConfig=workflow_config_message,
        updateMask=",".join(changed_fields),
    )
