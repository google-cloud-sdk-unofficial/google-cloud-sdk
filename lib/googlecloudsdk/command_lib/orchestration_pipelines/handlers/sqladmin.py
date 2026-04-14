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
"""SQLAdmin resource handler."""

from typing import Any

from apitools.base.protorpclite import messages
from googlecloudsdk.api_lib.sql import operations as sql_operations
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class SqladminInstanceHandler(base.GcpResourceHandler):
  """Handler for SQLAdmin Instance resources."""

  _documentation_uri = (
      "https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/instances"
  )
  description = "SQLAdmin Instance resources."

  api_prefix = ""
  api_client_collection_path = "instances"

  @property
  def resource_message_type(self) -> type[messages.Message]:
    return self.messages.DatabaseInstance

  def build_get_request(self) -> messages.Message:
    return self.messages.SqlInstancesGetRequest(
        project=self.environment.project, instance=self.get_resource_id()
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    resource_message.name = self.get_resource_id()
    resource_message.project = self.environment.project
    return self.messages.SqlInstancesInsertRequest(
        project=self.environment.project, databaseInstance=resource_message
    )

  def build_delete_request(
      self, existing_resource: messages.Message
  ) -> messages.Message:
    return self.messages.SqlInstancesDeleteRequest(
        project=self.environment.project, instance=self.get_resource_id()
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    return self.messages.SqlInstancesPatchRequest(
        project=self.environment.project,
        instance=self.get_resource_id(),
        databaseInstance=resource_message,
    )

  def get_operation_method(self) -> Any:
    return self.client.operations.Get

  def build_operation_request(self, operation: Any) -> messages.Message:
    return self.messages.SqlOperationsGetRequest(
        project=self.environment.project,
        operation=operation.name,
    )

  def wait_for_operation(self, api_response: Any) -> Any:
    if api_response is None:
      return None

    if type(api_response).__name__ == "Operation":
      try:
        # We know we are always returning an SqlOperationsGetRequest, so we can
        # bypass resources.REGISTRY.Parse and build the ref directly.
        operation_ref = resources.REGISTRY.Create(
            "sql.operations",
            operation=api_response.name,
            project=self.environment.project,
        )
      except resources.Error:
        return api_response

      log.status.Print(
          f"     Waiting for operation {api_response.name} to complete..."
      )

      try:
        api_response = sql_operations.OperationsV1Beta4.WaitForOperation(
            self.client,
            operation_ref,
            "Waiting for sqladmin.instance operation to complete",
        )
      except sql_operations.exceptions.OperationError as e:
        log.error(f"Operation failed: {e}")

    return api_response


class SqladminDatabaseHandler(base.GcpResourceHandler):
  """Handler for SQLAdmin Database resources."""

  _documentation_uri = (
      "https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/databases"
  )
  description = "SQLAdmin Database resources."

  api_prefix = ""
  api_client_collection_path = "databases"

  def build_get_request(self) -> messages.Message:
    return self.messages.SqlDatabasesGetRequest(
        project=self.environment.project,
        instance=self.get_validated_parent_id(),
        database=self.get_resource_id(),
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    resource_message.project = self.environment.project
    resource_message.instance = self.get_validated_parent_id()
    resource_message.name = self.get_resource_id()
    return resource_message

  def build_delete_request(
      self, existing_resource: messages.Message
  ) -> messages.Message:
    return self.messages.SqlDatabasesDeleteRequest(
        project=self.environment.project,
        instance=self.get_validated_parent_id(),
        database=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    return self.messages.SqlDatabasesPatchRequest(
        project=self.environment.project,
        instance=self.get_validated_parent_id(),
        database=self.get_resource_id(),
        databaseResource=resource_message,
    )

  def get_update_method(self) -> Any:
    return self._api_client_collection.Patch

  def get_operation_method(self) -> Any:
    return self.client.operations.Get

  def build_operation_request(self, operation: Any) -> messages.Message:
    return self.messages.SqlOperationsGetRequest(
        project=self.environment.project,
        operation=operation.name,
    )


class SqladminUserHandler(base.GcpResourceHandler):
  """Handler for SQLAdmin User resources."""

  _documentation_uri = (
      "https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/users"
  )
  description = "SQLAdmin User resources."

  api_prefix = ""
  api_client_collection_path = "users"

  def build_get_request(self) -> messages.Message:
    return self.messages.SqlUsersGetRequest(
        project=self.environment.project,
        instance=self.get_validated_parent_id(),
        name=self.get_resource_id(),
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    resource_message.project = self.environment.project
    resource_message.instance = self.get_validated_parent_id()
    return resource_message

  def build_delete_request(
      self, existing_resource: messages.Message
  ) -> messages.Message:
    # The API requires host but we might not have it from ID.
    # Using empty string per CLI behavior.
    return self.messages.SqlUsersDeleteRequest(
        project=self.environment.project,
        instance=self.get_validated_parent_id(),
        name=self.get_resource_id(),
        host="",
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    return self.messages.SqlUsersUpdateRequest(
        project=self.environment.project,
        instance=self.get_validated_parent_id(),
        name=self.get_resource_id(),
        user=resource_message,
    )

  def get_update_method(self) -> Any:
    # SqlUsers uses Update instead of Patch
    return self._api_client_collection.Update

  def get_operation_method(self) -> Any:
    return self.client.operations.Get

  def build_operation_request(self, operation: Any) -> messages.Message:
    return self.messages.SqlOperationsGetRequest(
        project=self.environment.project,
        operation=operation.name,
    )
