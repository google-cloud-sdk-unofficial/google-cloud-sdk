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

from typing import Any

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base as handlers_base
from googlecloudsdk.core import log


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
) -> None:
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

  api_response = handler.get_create_method()(request=request)
  api_response = handler.wait_for_operation(api_response)
  handler.post_deploy(api_response, created=True)
  success_message = handler.get_success_deployment_message(api_response)
  log.status.Print(
      f"     Successfully created {resource_type_name}: {success_message}"
  )


def _handle_existing_resource(
    handler: handlers_base.GcpResourceHandler,
    existing_resource: Any,
    local_definition: Any,
    resource_type_name: str,
) -> None:
  """Handles updating, skipping, or recreating an existing GCP resource."""
  if handler.resource.update_action == "skip":
    log.status.Print(
        f"     Found existing {resource_type_name}. Skipping update based on "
        "updateAction."
    )
    return

  log.status.Print(
      f"     Found existing {resource_type_name}. Comparing configurations..."
  )
  changed_fields = handler.compare(existing_resource, local_definition)
  if not changed_fields:
    capitalized_type = resource_type_name[0].upper() + resource_type_name[1:]
    log.status.Print(f"     {capitalized_type} is already up-to-date.")
    return

  if handler.resource.update_action == "recreate":
    log.status.Print(
        f"     Differences found in fields: {', '.join(changed_fields)}. "
        "Recreating..."
    )
    _delete_resource(handler, existing_resource, resource_type_name)

    log.status.Print(
        f"     Creating new {resource_type_name} after deletion..."
    )
    _create_resource(handler, local_definition, resource_type_name)
  else:
    log.status.Print(
        f"     Differences found in fields: {', '.join(changed_fields)}. "
        "Patching..."
    )
    _update_resource(
        handler,
        existing_resource,
        local_definition,
        changed_fields,
        resource_type_name,
    )


def validate_gcp_resource_l1(handler: handlers_base.GcpResourceHandler) -> None:
  """Validates GCP resource L1 (Can it be converted to One Platform message)."""
  resource_id = handler.get_resource_id()
  resource_type_name = handler.resource.type
  log.status.Print(
      f"     Checking schema for {resource_type_name}: '{resource_id}'"
  )
  try:
    local_definition = handler.get_local_definition()
    handler.to_resource_message(local_definition)
    log.status.Print(f"     {resource_type_name} schema is valid.")
  except Exception as e:
    raise ValueError(
        f"Validation failed for resource '{resource_id}' of type"
        f" '{resource_type_name}': {e}"
    ) from e


def validate_gcp_resource_l2(handler: handlers_base.GcpResourceHandler) -> None:
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
          f"     {resource_type_name} not found in cloud. Will be created."
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


def deploy_gcp_resource(handler: handlers_base.GcpResourceHandler) -> None:

  """Deploys a GCP resource using the given handler."""
  resource_id = handler.get_resource_id()
  resource_type_name = handler.resource.type
  log.status.Print(
      f"     Checking for existing {resource_type_name}: '{resource_id}'"
  )
  try:
    existing_resource = handler.find_existing_resource()
    local_definition = handler.get_local_definition()
    if existing_resource:
      _handle_existing_resource(
          handler, existing_resource, local_definition, resource_type_name
      )
    else:
      capitalized_type = resource_type_name[0].upper() + resource_type_name[1:]
      log.status.Print(
          f"     {capitalized_type} not found. Creating a new one..."
      )
      _create_resource(handler, local_definition, resource_type_name)

  except (
      apitools_exceptions.HttpError,
      ValueError,
      NotImplementedError,
  ) as e:
    raise ValueError(
        f"Failed to deploy resource '{resource_id}' of type"
        f" '{resource_type_name}': {e}"
    ) from e
