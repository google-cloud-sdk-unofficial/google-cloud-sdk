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

from typing import Any, Dict

from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base


class DataformRepositoryHandler(base.GcpResourceHandler):
  """Handler for Dataform Repository resources."""

  def build_get_request(self) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesGetRequest(
        name=self._get_resource_name()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesCreateRequest(
        parent=self._get_location_path(),
        repository=resource_message,
        repositoryId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    resource_message.name = existing_resource.name
    return self.messages.DataformProjectsLocationsRepositoriesPatchRequest(
        name=existing_resource.name,
        repository=resource_message,
        updateMask=",".join(changed_fields),
    )


class DataformReleaseConfigHandler(base.GcpResourceHandler):
  """Handler for Dataform ReleaseConfig resources."""

  def build_get_request(self) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesReleaseConfigsGetRequest(
        name=self._get_resource_name()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesReleaseConfigsCreateRequest(
        parent=self._get_location_path(),
        releaseConfig=resource_message,
        releaseConfigId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    resource_message.name = existing_resource.name
    return self.messages.DataformProjectsLocationsRepositoriesReleaseConfigsPatchRequest(
        name=existing_resource.name,
        releaseConfig=resource_message,
        updateMask=",".join(changed_fields),
    )


class DataformWorkflowConfigHandler(base.GcpResourceHandler):
  """Handler for Dataform WorkflowConfig resources."""

  def build_get_request(self) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesWorkflowConfigsGetRequest(
        name=self._get_resource_name()
    )

  def get_local_definition(self) -> Dict[str, Any]:
    definition = super().get_local_definition()
    if ("releaseConfig" in definition and
        "/" not in definition["releaseConfig"]):
      release_config_id = definition["releaseConfig"]
      definition["releaseConfig"] = (
          f"{self._get_location_path()}/releaseConfigs/{release_config_id}"
      )
    return definition

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesWorkflowConfigsCreateRequest(
        parent=self._get_location_path(),
        workflowConfig=resource_message,
        workflowConfigId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    resource_message.name = existing_resource.name
    return self.messages.DataformProjectsLocationsRepositoriesWorkflowConfigsPatchRequest(
        name=existing_resource.name,
        workflowConfig=resource_message,
        updateMask=",".join(changed_fields),
    )
