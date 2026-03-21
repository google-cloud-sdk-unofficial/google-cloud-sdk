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
from typing import Any, Optional, Tuple, Union

from apitools.base.protorpclite import messages
from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.orchestration_pipelines import deployment_model
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class GcpResourceHandler(abc.ABC):
  """An abstract handler for deploying a specific type of GCP resource."""

  api_name = None
  api_version = None
  api_prefix = "projects_locations"
  api_client_collection_path = None
  collection_name = None

  def __init__(
      self,
      resource: deployment_model.ResourceModel,
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

  @property
  def _api_name(self) -> str:
    if self.api_name is not None:
      return self.api_name
    return self.resource.type.split(".")[0]

  @property
  def _api_version(self) -> str:
    if self.api_version is not None:
      return self.api_version
    # fallback to ResourceModel's api_version if available
    if self.resource.api_version is not None:
      return self.resource.api_version
    # otherwise find gcloud default
    return apis.ResolveVersion(self._api_name)

  def _get_location_path(self) -> str:
    location_path = f"projects/{self.environment.project}/locations/{self.environment.region}"
    if self.resource.parent:
      return f"{location_path}{self.resource.parent}"
    return location_path

  def _get_client(self):
    return apis.GetClientInstance(self._api_name, self._api_version)

  def _get_messages(self):
    return apis.GetMessagesModule(self._api_name, self._api_version)

  def get_resource_id(self) -> str:
    """Returns the unique identifier for the resource."""
    return self.resource.name

  def _pluralize(self, word: str) -> str:
    """Returns the pluralized form of a word."""
    if word.endswith("y"):
      return word[:-1] + "ies"
    return word + "s"

  @property
  def _collection_name(self) -> str:
    if self.collection_name is not None:
      return self.collection_name
    return self._pluralize(self.resource.type.split(".")[-1])

  @property
  def _api_client_collection_path(self) -> str:
    """Returns the path to the API collection on the client."""
    if self.api_client_collection_path is not None:
      return self.api_client_collection_path

    parts = self.resource.type.split(".")[1:]
    pluralized_parts = []
    for i, part in enumerate(parts):
      if i == len(parts) - 1 and self.collection_name is not None:
        pluralized_parts.append(self.collection_name)
      else:
        pluralized_parts.append(self._pluralize(part))

    return "_".join([self.api_prefix] + pluralized_parts)

  def _get_resource_name(self) -> str:
    """Returns the full resource name including location and collection."""
    return f"{self._get_location_path()}/{self._collection_name}/{self.get_resource_id()}"

  def find_existing_resource(self) -> Any:
    """Finds the existing resource on GCP."""
    request = self.build_get_request()
    try:
      return self._api_client_collection.Get(request)
    except apitools_exceptions.HttpNotFoundError:
      return None

  @abc.abstractmethod
  def build_get_request(self) -> messages.Message:
    """Builds the API request to get the resource."""

  def get_local_definition(self) -> dict[str, Any]:
    definition = self.resource.definition
    return definition.copy() if definition else {}

  @property
  def resource_message_type(self) -> type[messages.Message]:
    """Returns the apitools Message type for the resource."""
    # Try to infer from resource type
    # e.g. iam.serviceAccount -> ServiceAccount
    # e.g. dataform.repository.releaseConfig -> ReleaseConfig
    try:
      short_type = self.resource.type.split(".")[-1]
      # Uppercase first letter
      message_name = short_type[0].upper() + short_type[1:]
      if hasattr(self.messages, message_name):
        return getattr(self.messages, message_name)
    except (IndexError, AttributeError):
      pass

    raise NotImplementedError(
        f"Could not infer message type for {self.resource.type}, "
        "please override resource_message_type"
    )

  def to_resource_message(self, definition: dict[str, Any]) -> messages.Message:
    """Converts a dictionary definition to a resource message."""
    return encoding.DictToMessage(definition, self.resource_message_type)

  @abc.abstractmethod
  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    """Builds the API request to create the resource."""

  @abc.abstractmethod
  def build_update_request(
      self,
      existing_resource: Union[messages.Message, dict[str, Any]],
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    """Builds the API request to update the resource."""

  @property
  def _api_client_collection(self) -> Any:
    return getattr(self.client, self._api_client_collection_path)

  def get_create_method(self) -> Any:
    """Returns the client method used to create the resource."""
    return self._api_client_collection.Create

  def get_update_method(self) -> Any:
    """Returns the client method used to update the resource."""
    return self._api_client_collection.Patch

  def compare(
      self, existing_resource: Any, local_definition: dict[str, Any]
  ) -> list[str]:
    """Compares existing resource with local definition."""
    existing_dict = existing_resource
    # If the resource is an apitools Message, convert it to a dict.
    if not isinstance(existing_resource, dict):
      try:
        existing_dict = encoding.MessageToDict(existing_resource)
      except Exception:  # pylint: disable=broad-except
        # Fallback for non-Message objects (e.g. in tests/mocks)
        if hasattr(existing_resource, "__dict__"):
          existing_dict = existing_resource.__dict__

    return self._compare_recursive(existing_dict, local_definition, "")

  def _compare_recursive(
      self, existing: Any, local: Any, prefix: str
  ) -> list[str]:
    """Recursively compares two objects and returns changed fields."""
    diffs = []
    is_local_dict = isinstance(local, dict)
    is_existing_dict = isinstance(existing, dict)

    if is_local_dict:
      if not is_existing_dict:
        # If existing is not a dict, the whole tree at 'prefix' matches nothing
        # useful in structure, so we report the prefix itself (or local keys).
        return [prefix] if prefix else list(local.keys())

      for k, v in local.items():
        next_prefix = f"{prefix}.{k}" if prefix else k
        if k not in existing:
          diffs.append(next_prefix)
        else:
          diffs.extend(self._compare_recursive(existing[k], v, next_prefix))
    else:
      # List or Primitive
      if existing != local:
        return [prefix] if prefix else []

    return diffs

  def wait_for_operation(
      self, operation: Any
  ) -> Tuple[Any, Optional[str]]:
    """Waits for long running operation if applicable.

    The default implementation handles resources that don't return LROs.
    It returns the operation as is, and resource name for name_to_print.
    Handlers for resources that return LROs should override this method.

    Args:
      operation: The operation to wait for, or the result if no LRO.

    Returns:
      A tuple containing the completed operation and a name to print.
    """
    if type(operation).__name__ == "Operation":
      if getattr(operation, "done", False):
        return operation, self.resource.name

      op_name = getattr(operation, "name", "unknown")
      log.status.Print(f"     Waiting for operation {op_name} to complete...")

      # Determine collection for the operation based on the current api client
      operation_collection = f"{self.api_prefix}_operations".replace("_", ".")
      if not operation_collection.startswith(self._api_name):
        operation_collection = f"{self._api_name}.{operation_collection}"

      try:
        operation_ref = resources.REGISTRY.Parse(
            operation.name,
            collection=operation_collection,
        )
      except resources.Error:
        # Fallback if parse fails
        return operation, getattr(operation, "name", self.resource.name)

      operation_service_name = f"{self.api_prefix}_operations"
      if not hasattr(self.client, operation_service_name):
        raise ValueError(
            f"Operation service {operation_service_name} not found on client "
            f"for {self._api_name}."
        )
      ops_service = getattr(self.client, operation_service_name)

      poller = waiter.CloudOperationPollerNoResources(ops_service)
      try:
        operation = waiter.WaitFor(
            poller,
            operation_ref,
            f"Waiting for {self._api_name} operation",
        )
      except waiter.TimeoutError:
        log.error(f"Timed out waiting for {self._api_name} operation.")
    return operation, self.resource.name
