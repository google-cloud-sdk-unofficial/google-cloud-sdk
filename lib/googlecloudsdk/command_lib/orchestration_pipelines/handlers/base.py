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
"""Base class for GCP resource handlers."""

import abc
from typing import Any, Optional, Tuple
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.orchestration_pipelines import deployment_model


class GcpResourceHandler(abc.ABC):
  """An abstract handler for deploying a specific type of GCP resource."""

  api_name = None
  api_version = None

  def __init__(
      self,
      resource: deployment_model.AnyResource,
      environment: deployment_model.EnvironmentModel,
      dry_run: bool,
      debug: bool = False,
      show_requests: bool = False,
  ):
    self.resource = resource
    self.environment = environment
    self.dry_run = dry_run
    self.debug = debug
    self.show_requests = show_requests
    self.client = self._get_client()
    self.messages = self._get_messages()

  def _get_client(self):
    if self.api_name is None or self.api_version is None:
      raise NotImplementedError("api_name and api_version must be set")
    return apis.GetClientInstance(self.api_name, self.api_version)

  def _get_messages(self):
    if self.api_name is None or self.api_version is None:
      raise NotImplementedError("api_name and api_version must be set")
    return apis.GetMessagesModule(self.api_name, self.api_version)

  @abc.abstractmethod
  def get_resource_id(self) -> str:
    """Returns the unique identifier for the resource."""

  @abc.abstractmethod
  def find_existing_resource(self) -> Any:
    """Finds the existing resource on GCP."""

  def get_local_definition(self) -> dict[str, Any]:
    definition = getattr(self.resource, "definition", None)
    return definition.copy() if definition else {}

  @abc.abstractmethod
  def build_create_request(self, definition: dict[str, Any]) -> Any:
    """Builds the API request to create the resource."""

  @abc.abstractmethod
  def build_update_request(
      self,
      existing_resource: Any,
      definition: dict[str, Any],
      changed_fields: list[str],
  ) -> Any:
    """Builds the API request to update the resource."""

  @abc.abstractmethod
  def get_create_method(self) -> Any:
    """Returns the client method used to create the resource."""

  @abc.abstractmethod
  def get_update_method(self) -> Any:
    """Returns the client method used to update the resource."""

  def compare(
      self, existing_resource: Any, local_definition: dict[str, Any]
  ) -> list[str]:
    return [
        k
        for k, v in local_definition.items()
        if getattr(existing_resource, k, None) != v
    ]

  def wait_for_operation(
      self, operation: Any
  ) -> Tuple[Any, Optional[str]]:
    """Waits for long running operation if applicable and returns result and name.

    The default implementation handles resources that don't return LROs.
    It returns the operation as is, and resource name for name_to_print.
    Handlers for resources that return LROs should override this method.

    Args:
      operation: The operation to wait for, or the result if no LRO.

    Returns:
      A tuple containing the completed operation and a name to print.
    """
    return operation, getattr(operation, "name", None)
