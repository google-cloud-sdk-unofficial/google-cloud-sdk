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
"""BigQuery Database and Table resource handler."""

from typing import Any, List

from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base


class BqDatasetHandler(base.GcpResourceHandler):
  """Handler for migrating BigQuery Dataset configurations."""

  api_prefix = ""
  description = (
      "BigQuery Dataset configurations.\n"
      "Definition handling:\n"
      " - datasetReference: automatically populated with project "
      "and dataset IDs"
  )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_get_request(self) -> messages.Message:
    return self.messages.BigqueryDatasetsGetRequest(
        projectId=self.environment.project,
        datasetId=self.resource.name
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    # The datasetReference must match projectId and datasetId.
    if not resource_message.datasetReference:
      resource_message.datasetReference = self.messages.DatasetReference()
    resource_message.datasetReference.projectId = self.environment.project
    resource_message.datasetReference.datasetId = self.resource.name

    return self.messages.BigqueryDatasetsInsertRequest(
        projectId=self.environment.project,
        dataset=resource_message,
    )

  def build_update_request(
      self,
      existing_resource: Any,
      resource_message: messages.Message,
      changed_fields: List[str],
  ) -> messages.Message:
    resource_message.datasetReference = existing_resource.datasetReference

    return self.messages.BigqueryDatasetsPatchRequest(
        projectId=self.environment.project,
        datasetId=self.resource.name,
        dataset=resource_message,
    )


class BqTableHandler(base.GcpResourceHandler):
  """Handler for migrating BigQuery Table configurations."""

  api_prefix = ""
  description = (
      "BigQuery Table configurations.\n"
      "Definition handling:\n"
      " - tableReference: automatically populated with project, "
      "dataset, and table IDs"
  )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_get_request(self) -> messages.Message:
    return self.messages.BigqueryTablesGetRequest(
        projectId=self.environment.project,
        datasetId=self.get_validated_parent_id(),
        tableId=self.resource.name,
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    if not resource_message.tableReference:
      resource_message.tableReference = self.messages.TableReference()
    resource_message.tableReference.projectId = self.environment.project
    resource_message.tableReference.datasetId = self.get_validated_parent_id()
    resource_message.tableReference.tableId = self.resource.name

    return self.messages.BigqueryTablesInsertRequest(
        projectId=self.environment.project,
        datasetId=self.get_validated_parent_id(),
        table=resource_message,
    )

  def build_update_request(
      self,
      existing_resource: Any,
      resource_message: messages.Message,
      changed_fields: List[str],
  ) -> messages.Message:
    resource_message.tableReference = existing_resource.tableReference

    return self.messages.BigqueryTablesPatchRequest(
        projectId=self.environment.project,
        datasetId=self.get_validated_parent_id(),
        tableId=self.resource.name,
        table=resource_message,
    )


class BqRoutineHandler(base.GcpResourceHandler):
  """Handler for migrating BigQuery Routine configurations."""

  description = "BigQuery Routine configurations."
  api_prefix = ""

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def get_update_method(self) -> Any:
    return self._api_client_collection.Update

  def build_get_request(self) -> messages.Message:
    return self.messages.BigqueryRoutinesGetRequest(
        projectId=self.environment.project,
        datasetId=self.get_validated_parent_id(),
        routineId=self.resource.name,
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    if not resource_message.routineReference:
      resource_message.routineReference = self.messages.RoutineReference()
    resource_message.routineReference.projectId = self.environment.project
    resource_message.routineReference.datasetId = self.get_validated_parent_id()
    resource_message.routineReference.routineId = self.resource.name

    return self.messages.BigqueryRoutinesInsertRequest(
        projectId=self.environment.project,
        datasetId=self.get_validated_parent_id(),
        routine=resource_message,
    )

  def build_update_request(
      self,
      existing_resource: Any,
      resource_message: messages.Message,
      changed_fields: List[str],
  ) -> messages.Message:
    resource_message.routineReference = existing_resource.routineReference

    return self.messages.BigqueryRoutinesUpdateRequest(
        projectId=self.environment.project,
        datasetId=self.get_validated_parent_id(),
        routineId=self.resource.name,
        routine=resource_message,
    )
