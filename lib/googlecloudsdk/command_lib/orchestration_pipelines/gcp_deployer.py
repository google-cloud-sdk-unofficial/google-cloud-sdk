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
"""A generic, object-oriented deployer for Google Cloud resources."""

import re
from typing import Any

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base as handlers_base
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import log
from googlecloudsdk.core.util import retry


def _delete_resource(
    handler: handlers_base.GcpResourceHandler,
    existing_resource: Any,
    resource_type_name: str,
) -> None:
  """Deletes a GCP resource and waits for the operation to complete."""
  delete_request = handler.build_delete_request(existing_resource)
  api_response = handler.get_delete_method()(request=delete_request)
  handler.wait_for_operation(api_response)
  log.status.Print(f"     Successfully deleted {resource_type_name}.")


def _update_resource(
    handler: handlers_base.GcpResourceHandler,
    existing_resource: Any,
    local_definition: Any,
    changed_fields: list[str],
    resource_type_name: str,
) -> Any:
  """Updates a GCP resource and waits for the operation to complete."""
  resource_message = handler.to_resource_message(local_definition)
  try:
    request = handler.build_update_request(
        existing_resource, resource_message, changed_fields
    )

    api_response = handler.get_update_method()(request=request)
    api_response = handler.wait_for_operation(api_response)
    handler.post_deploy(api_response, created=False)
    success_message = handler.get_success_deployment_message(api_response)
    log.status.Print(
        f"     Successfully updated {resource_type_name}: {success_message}"
    )
    return api_response
  except NotImplementedError as e:
    raise ValueError(
        "This resource does not support patch updates. "
        "Please set `updateAction: recreate` in your deployment "
        "model to recreate the resource when it changes."
    ) from e


def _create_resource(
    handler: handlers_base.GcpResourceHandler,
    local_definition: Any,
    resource_type_name: str,
) -> None:
  """Creates a new GCP resource and waits for the operation to complete."""
  resource_message = handler.to_resource_message(local_definition)
  request = handler.build_create_request(resource_message)

  def _try_create():
    api_response = handler.get_create_method()(request=request)
    api_response = handler.wait_for_operation(api_response)
    handler.post_deploy(api_response, created=True)
    return api_response

  def _should_retry(exc_type, exc_value, exc_traceback, state):
    del exc_type, exc_traceback, state  # Unused
    return handler.should_retry_create(exc_value)

  retryer = retry.Retryer(max_wait_ms=120000, exponential_sleep_multiplier=1.5)
  try:
    api_response = retryer.RetryOnException(
        _try_create,
        should_retry_if=_should_retry,
        sleep_ms=10000,
    )
    success_message = handler.get_success_deployment_message(api_response)
    log.status.Print(
        f"     Successfully created {resource_type_name}: {success_message}"
    )
    return api_response
  except retry.WaitException as e:
    raise ValueError(
        f"Failed to create {resource_type_name} due to timeout: {e}"
    ) from e


def _handle_existing_resource(
    handler: handlers_base.GcpResourceHandler,
    existing_resource: Any,
    local_definition: Any,
    resource_type_name: str,
) -> Any:
  """Handles updating, skipping, or recreating an existing GCP resource."""
  if handler.resource.update_action == "skip":
    log.status.Print(
        f"     Found existing {resource_type_name}. Skipping update based on "
        "updateAction."
    )
    return existing_resource

  log.status.Print(
      f"     Found existing {resource_type_name}. Comparing configurations..."
  )
  changed_fields = handler.compare(existing_resource, local_definition)
  if not changed_fields:
    capitalized_type = resource_type_name[0].upper() + resource_type_name[1:]
    log.status.Print(f"     {capitalized_type} is already up-to-date.")
    return existing_resource

  if handler.resource.update_action == "recreate":
    log.status.Print(
        f"     Differences found in fields: {', '.join(changed_fields)}. "
        "Recreating..."
    )
    _delete_resource(handler, existing_resource, resource_type_name)

    log.status.Print(
        f"     Creating new {resource_type_name} after deletion..."
    )
    return _create_resource(handler, local_definition, resource_type_name)
  else:
    log.status.Print(
        f"     Differences found in fields: {', '.join(changed_fields)}. "
        "Patching..."
    )
    return _update_resource(
        handler,
        existing_resource,
        local_definition,
        changed_fields,
        resource_type_name,
    )


def validate_gcp_resource_l1(
    handler: handlers_base.GcpResourceHandler, local_definition: Any = None
) -> None:
  """Validates GCP resource L1 (Can it be converted to One Platform message).

  Args:
    handler: The handler for the specific resource type.
    local_definition: The resource definition from the YAML file after template
      resolution. If None, it will be fetched from the handler.
  """
  resource_id = handler.get_resource_id()
  resource_type_name = handler.resource.type
  log.status.Print(
      f"     Checking schema for {resource_type_name}: '{resource_id}'"
  )
  try:
    if local_definition is None:
      local_definition = handler.get_local_definition()
    handler.to_resource_message(local_definition)
    log.status.Print(f"     {resource_type_name} schema is valid.")
  except Exception as e:
    raise ValueError(
        f"Validation failed for resource '{resource_id}' of type"
        f" '{resource_type_name}': {e}"
    ) from e


def validate_gcp_resource_l2(
    handler: handlers_base.GcpResourceHandler, dynamic_variables: dict[str, Any]
) -> None:
  """Validates GCP resource L2 (Does it exist in GCP and what are diffs)."""
  resource_id = handler.get_resource_id()
  resource_type_name = handler.resource.type
  log.status.Print(
      f"     Checking existence of {resource_type_name}: '{resource_id}'"
  )
  try:
    existing_resource = handler.find_existing_resource()
    local_definition = handler.get_local_definition()
    if existing_resource:
      _capture_resource_values(handler, dynamic_variables, existing_resource)
      log.status.Print(
          f"     Found existing {resource_type_name}. "
          "Comparing configurations..."
      )
      changed_fields = handler.compare(existing_resource, local_definition)
      if changed_fields:
        fields_str = ", ".join(changed_fields)
        log.status.Print(f"     Differences found in fields: {fields_str}")
        if handler.resource.update_action == "recreate":
          try:
            handler.get_delete_method()
          except NotImplementedError as e:
            raise ValueError(
                f"Validation failed for resource '{resource_id}': "
                "Update mode is set to 'recreate' but the resource type "
                f"'{resource_type_name}' does not support deletion."
            ) from e
        elif handler.resource.update_action != "skip":
          try:
            handler.get_update_method()
          except NotImplementedError as e:
            raise ValueError(
                f"Validation failed for resource '{resource_id}': "
                "Update mode is set to patch but the resource type "
                f"'{resource_type_name}' does not support patch updates. "
                "Please set `updateAction: recreate`."
            ) from e
      else:
        log.status.Print(f"     {resource_type_name} is up-to-date in cloud.")
    else:
      log.status.Print(
          f"     {resource_type_name} not found in cloud. "
          "It will be created during deploy. Dependent resources and pipelines "
          "validation may fail."
      )
  except (
      apitools_exceptions.HttpError,
      ValueError,
      NotImplementedError,
  ) as e:
    raise ValueError(
        f"Validation failed for resource '{resource_id}' of type"
        f" '{resource_type_name}': {e}"
    ) from e


def _get_field_value(data: Any, field_path: str) -> Any:
  """Extracts value from a dict or object using a dotted path."""
  parts = field_path.split(".")
  current = data
  for part in parts:
    if isinstance(current, dict):
      current = current.get(part)
    elif hasattr(current, part):
      val = getattr(current, part)
      current = val if not callable(val) else None
    else:
      return None
  return current


def _capture_resource_values(
    handler: handlers_base.GcpResourceHandler,
    dynamic_variables: dict[str, Any],
    deployed_resource: Any,
) -> None:
  """Captures values from a deployed resource and updates dynamic_variables."""
  if not hasattr(handler.resource, "capture") or not handler.resource.capture:
    return

  if not deployed_resource:
    log.warning(
        f"Could not find deployed resource '{handler.get_resource_id()}' to"
        " capture values."
    )
    return

  deployed_dict = deployed_resource
  if not isinstance(deployed_resource, dict):
    try:
      deployed_dict = encoding.MessageToDict(deployed_resource)
    except (AttributeError, TypeError):
      if hasattr(deployed_resource, "__dict__"):
        deployed_dict = deployed_resource.__dict__

  for c in handler.resource.capture:
    var_name = c.variable
    if var_name in dynamic_variables:
      log.info(f"Skipping capture for '{var_name}' as it already exists.")
      continue

    field_path = c.field
    val = _get_field_value(deployed_dict, field_path)
    if val is None:
      log.warning(
          f"Field '{field_path}' not found in resource"
          f" '{handler.get_resource_id()}'."
      )
      continue

    if c.regex:
      match = re.search(c.regex, str(val))
      if match:
        if match.groups():
          val = match.group(1)  # First group
        else:
          val = match.group(0)  # Full match
      else:
        log.warning(
            f"Regex '{c.regex}' did not match value '{val}' for field"
            f" '{field_path}' in resource '{handler.get_resource_id()}'."
        )
        val = None

    if val is not None:
      dynamic_variables[var_name] = val
      log.debug(f"Captured value for '{var_name}': {val}")


def deploy_gcp_resource(
    handler: handlers_base.GcpResourceHandler, dynamic_variables: dict[str, Any]
) -> None:
  """Deploys a GCP resource using the given handler."""
  resource_id = handler.get_resource_id()
  resource_type_name = handler.resource.type

  local_definition = handler.get_local_definition()
  if local_definition:
    local_definition = yaml_processor.resolve_templates_in_dict(
        local_definition, dynamic_variables
    )

  validate_gcp_resource_l1(handler, local_definition)

  log.status.Print(
      f"     Checking for existing {resource_type_name}: '{resource_id}'"
  )
  try:
    existing_resource = handler.find_existing_resource()
    deployed_resource = None
    if existing_resource:
      deployed_resource = _handle_existing_resource(
          handler, existing_resource, local_definition, resource_type_name
      )
    else:
      capitalized_type = resource_type_name[0].upper() + resource_type_name[1:]
      log.status.Print(
          f"     {capitalized_type} not found. Creating a new one..."
      )
      deployed_resource = _create_resource(
          handler, local_definition, resource_type_name
      )

    _capture_resource_values(handler, dynamic_variables, deployed_resource)

  except (
      apitools_exceptions.HttpError,
      ValueError,
      NotImplementedError,
  ) as e:
    raise ValueError(
        f"Failed to deploy resource '{resource_id}' of type"
        f" '{resource_type_name}': {e}"
    ) from e
