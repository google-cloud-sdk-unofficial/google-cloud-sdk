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
import dataclasses
from typing import Any, Union

from apitools.base.protorpclite import messages
from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.orchestration_pipelines import deployment_model
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


IMPLICIT_LABEL_KEY = "orchestration_pipeline"
IMPLICIT_LABEL_VALUE = "true"


class GcpResourceHandler(abc.ABC):
  """An abstract handler for deploying a specific type of GCP resource."""

  api_name = None
  api_version = None
  api_prefix = "projects_locations"
  api_client_collection_path = None
  collection_name = None
  allowed_metadata = []

  # Documentation and Discoverability
  _parent_resource_type = None
  _documentation_uri = None

  def __init__(
      self,
      resource: deployment_model.ResourceModel,
      environment: deployment_model.EnvironmentModel,
      debug: bool = False,
  ):
    self.resource = resource
    self.environment = environment
    self.debug = debug
    self.client = self._get_client()
    self.messages = self._get_messages()
    self._validate_metadata()

  def get_labels_field_name(self) -> str | None:
    """Returns the name of the labels field, or None to disable.

    Subclasses can override this to specify a custom field name or disable
    implicit labeling by returning None. Returning "" (default) enables
    autodetection.
    """
    return ""

  def _detect_labels_field(self) -> str | None:
    """Detects the name of the labels field in the resource message."""
    override = self.get_labels_field_name()
    if override is None:
      return None
    if override:
      return override

    for field in self.resource_message_type.all_fields():
      if field.name == "labels":
        return "labels"
    return None

  def _build_labels_value(
      self, labels_value_type: Any, labels_dict: dict[str, str]
  ) -> Any:
    """Builds a LabelsValue message from a dictionary."""
    additional_properties = []
    for k, v in labels_dict.items():
      additional_properties.append(
          labels_value_type.AdditionalProperty(key=k, value=v)
      )
    return labels_value_type(additionalProperties=additional_properties)

  def _validate_metadata(self):
    """Validates that the resource metadata is applicable for this handler."""
    if not self.resource.metadata:
      return

    # attributes in MetadataModel that are not None
    used_metadata_keys = [
        f.name
        for f in dataclasses.fields(self.resource.metadata)
        if getattr(self.resource.metadata, f.name) is not None
    ]

    supported_metadata = {"location"}
    if self.allowed_metadata:
      supported_metadata.update(self.allowed_metadata)

    for key in used_metadata_keys:
      if key not in supported_metadata:
        msg = (
            f"Metadata field '{key}' is not applicable for resource type"
            f" '{self.resource.type}'."
        )
        if self.allowed_metadata:
          msg += f" Allowed metadata fields: {list(supported_metadata)}"
        else:
          msg += " This resource does not support any metadata fields."
        raise ValueError(msg)

    # Validate that nested resources have an explicit parent defined
    parts = self.resource.type.split(".")
    if len(parts) >= 3 and not self.resource.parent:
      parent_type = parts[-2]
      raise ValueError(
          f"Resource type '{self.resource.type}' represents a nested resource "
          f"and requires an explicit 'parent' (expected type: '{parent_type}') "
          "to be set in the resource configuration."
      )

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

  @property
  def location(self) -> str:
    """Returns the effective location (region/zone/global) for the resource.

    Checks metadata.location first, falls back to environment region.
    """
    if self.resource.metadata.location is not None:
      return self.resource.metadata.location
    return self.environment.region

  def _get_location_path(self) -> str:
    """Returns the base path for the API location."""
    return f"projects/{self.environment.project}/locations/{self.location}"

  def _get_parent_path(self) -> str:
    """Returns the path to the parent resource."""
    location_path = self._get_location_path()
    if self.resource.parent:
      parts = self.resource.type.split(".")
      if len(parts) >= 3:
        parent_type = self._pluralize(parts[-2])
        parent_id = self.get_validated_parent_id()
        return f"{location_path}/{parent_type}/{parent_id}"
      else:
        raise ValueError(
            "Cannot infer parent type from resource type "
            f"'{self.resource.type}'"
        )
    return location_path

  def _get_client(self):
    return apis.GetClientInstance(self._api_name, self._api_version)

  def _get_messages(self):
    return apis.GetMessagesModule(self._api_name, self._api_version)

  def get_validated_parent_id(self) -> str:
    """Extracts and validates the ID from a parent string.

    Expected format is 'parentId'.

    Returns:
      The validated parent ID.

    Raises:
      ValueError: If the parent is missing or the format is invalid (e.g.
        contains '/').
    """
    if not self.resource.parent:
      raise ValueError(f"Parent must be specified for {self.resource.type}.")

    parent = self.resource.parent.strip()
    if "/" in parent:
      raise ValueError(
          f"Resource parent '{self.resource.parent}' must not contain '/'."
      )

    return parent

  def get_resource_id(self) -> str:
    """Returns the unique identifier for the resource."""
    return self.resource.name

  @classmethod
  def _pluralize(cls, word: str) -> str:
    """Returns the pluralized form of a word."""
    if word.endswith("y") and word[-2:-1].lower() not in "aeiouy":
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

    if self.api_prefix:
      return "_".join([self.api_prefix] + pluralized_parts)
    return "_".join(pluralized_parts)

  def _get_resource_name(self) -> str:
    """Returns the full resource name including location and collection."""
    return f"{self._get_parent_path()}/{self._collection_name}/{self.get_resource_id()}"

  def find_existing_resource(self) -> Any:
    """Finds the existing resource on GCP."""
    request = self.build_get_request()
    try:
      return self.get_get_method()(request)
    except apitools_exceptions.HttpNotFoundError:
      return None

  def get_parent_resource_type(self) -> str:
    """Returns the type of the parent resource, or None if top-level."""
    if self._parent_resource_type is not None:
      return self._parent_resource_type

    type_name = self.resource.type
    parts = type_name.split(".")
    if len(parts) > 2:
      parent_type = ".".join(parts[:-1])
    else:
      parent_type = None

    return parent_type

  def get_documentation_uri(self) -> str:
    """Returns a link to the REST API documentation for this resource."""
    if self._documentation_uri is not None:
      return self._documentation_uri

    try:
      resource_type = self.resource.type
      api_name = self.api_name if self.api_name else resource_type.split(".")[0]
      api_version = self.api_version
      if not api_version:
        api_version = apis.ResolveVersion(api_name)

      if self.api_client_collection_path:
        collection_path = self.api_client_collection_path
      else:
        parts = resource_type.split(".")[1:]
        pluralized_parts = []
        for i, part in enumerate(parts):
          if i == len(parts) - 1 and self.collection_name is not None:
            pluralized_parts.append(self.collection_name)
          else:
            pluralized_parts.append(self._pluralize(part))

        if self.api_prefix:
          collection_path = "_".join([self.api_prefix] + pluralized_parts)
        else:
          collection_path = "_".join(pluralized_parts)

      collection_path = collection_path.replace("_", ".")
      return (
          f"https://cloud.google.com/{api_name}/docs/reference/rest/"
          f"{api_version}/{collection_path}"
      )
    except Exception:  # pylint: disable=broad-exception-caught
      return "N/A"

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
    definition_copy = definition.copy()
    labels_field_name = self._detect_labels_field()
    if labels_field_name:
      labels = definition_copy.get(labels_field_name, {})
      if isinstance(labels, dict):
        labels_copy = labels.copy()
        labels_copy[IMPLICIT_LABEL_KEY] = IMPLICIT_LABEL_VALUE
        definition_copy[labels_field_name] = labels_copy
    return encoding.DictToMessage(definition_copy, self.resource_message_type)

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

  def get_get_method(self) -> Any:
    """Returns the client method used to get the resource."""
    return self._api_client_collection.Get

  def get_delete_method(self) -> Any:
    """Returns the client method used to delete the resource."""
    return self._api_client_collection.Delete

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

    diffs = self._compare_recursive(existing_dict, local_definition, "")

    if diffs:
      labels_field_name = self._detect_labels_field()
      if labels_field_name and labels_field_name not in diffs:
        existing_labels = existing_dict.get(labels_field_name, {})
        if isinstance(existing_labels, dict):
          if existing_labels.get(IMPLICIT_LABEL_KEY) != IMPLICIT_LABEL_VALUE:
            diffs.append(labels_field_name)

    return diffs

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
    elif isinstance(local, list) and isinstance(existing, list):
      if len(local) != len(existing):
        return [prefix] if prefix else []
      for ext_item, loc_item in zip(existing, local):
        item_diffs = self._compare_recursive(ext_item, loc_item, prefix)
        if item_diffs:
          return [prefix] if prefix else []
    else:
      # Primitive
      if isinstance(existing, str) and isinstance(local, str):
        if existing != local:
          # Permit API URLs to match partial configuration paths natively
          if not (existing.startswith("https://") and existing.endswith(local)):
            return [prefix] if prefix else []
      elif str(existing) != str(local) and existing != local:
        return [prefix] if prefix else []

    return diffs

  def wait_for_operation(self, api_response: Any) -> Any:
    """Waits for long running operation if applicable.

    The default implementation handles resources that don't return LROs.
    It returns the api_response as is.
    Handlers for resources that return LROs should override this method.

    Args:
      api_response: The operation to wait for, or the resource if no LRO.

    Returns:
      The completed operation or the originally returned resource.
    """

    if type(api_response).__name__ == "Operation":
      if getattr(api_response, "done", False):
        return api_response

      op_name = getattr(api_response, "name", "unknown")
      log.status.Print(f"     Waiting for operation {op_name} to complete...")

      # Determine collection for the operation based on the current api client
      operation_collection = f"{self.api_prefix}_operations".replace("_", ".")
      if not operation_collection.startswith(self._api_name):
        operation_collection = f"{self._api_name}.{operation_collection}"

      try:
        operation_ref = resources.REGISTRY.Parse(
            api_response.name,
            collection=operation_collection,
        )
      except resources.Error:
        # Fallback if parse fails
        return api_response

      operation_service_name = f"{self.api_prefix}_operations"
      if not hasattr(self.client, operation_service_name):
        raise ValueError(
            f"Operation service {operation_service_name} not found on client "
            f"for {self._api_name}."
        )
      ops_service = getattr(self.client, operation_service_name)

      poller = waiter.CloudOperationPollerNoResources(ops_service)
      try:
        api_response = waiter.WaitFor(
            poller,
            operation_ref,
            f"Waiting for {self._api_name} operation",
        )
      except waiter.TimeoutError:
        log.error(f"Timed out waiting for {self._api_name} operation.")
    return api_response

  def get_success_deployment_message(self, api_response: Any) -> str:  # pylint: disable=unused-argument
    """Returns the identifier to print after successful resource deployment.

    Args:
      api_response: The API response returned by wait_for_operation or create.

    By default this returns the logical name defined in the local configuration.
    Subclasses should override this if the generated API identifier is required
    by users to track the resource (e.g. BQ DTS config IDs).
    """
    return self.resource.name

  def post_deploy(self, api_response: Any, created: bool) -> None:
    """Executes actions after a successful deployment.

    Args:
      api_response: The API response returned by the deployment operation.
      created: True if the resource was created, False if it was updated.
    """
    pass
