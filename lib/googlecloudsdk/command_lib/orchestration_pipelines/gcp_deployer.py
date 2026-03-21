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


def _print_padded_request(request: Any) -> None:
  """Prints a multi-line request object with consistent indentation."""
  for line in str(request).splitlines():
    log.status.Print(f"     {line}")


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
      log.status.Print(
          f"     Found existing {resource_type_name}. "
          "Comparing configurations..."
      )
      changed_fields = handler.compare(existing_resource, local_definition)
      if not changed_fields:
        capitalized_type = (
            resource_type_name[0].upper() + resource_type_name[1:]
        )
        log.status.Print(
            f"     {capitalized_type} is already up-to-date."
        )
        return
      log.status.Print(
          f"     Differences found in fields: {', '.join(changed_fields)}. "
          "Patching..."
      )
      resource_message = handler.to_resource_message(local_definition)
      request = handler.build_update_request(
          existing_resource, resource_message, changed_fields
      )

      if handler.dry_run:
        log.status.Print(f"     [DRY RUN] Would update {resource_type_name}")
        if handler.show_requests:
          _print_padded_request(request)
      else:
        if handler.show_requests:
          log.error("--- GCP API UPDATE REQUEST ---")
          _print_padded_request(request)
        api_response = handler.get_update_method()(request=request)
        api_response = handler.wait_for_operation(api_response)
        handler.post_deploy(api_response, created=False)
        success_message = handler.get_success_deployment_message(api_response)
        log.status.Print(
            f"     Successfully updated {resource_type_name}: {success_message}"
        )

    else:
      capitalized_type = resource_type_name[0].upper() + resource_type_name[1:]
      log.status.Print(
          f"     {capitalized_type} not found. Creating a new"
          " one..."
      )

      resource_message = handler.to_resource_message(local_definition)
      request = handler.build_create_request(resource_message)

      if handler.dry_run:
        log.status.Print(f"     [DRY RUN] Would create {resource_type_name}")
        if handler.show_requests:
          _print_padded_request(request)
      else:
        if handler.show_requests:
          log.error("--- GCP API CREATE REQUEST ---")
          _print_padded_request(request)
        api_response = handler.get_create_method()(request=request)
        api_response = handler.wait_for_operation(api_response)
        handler.post_deploy(api_response, created=True)
        success_message = handler.get_success_deployment_message(api_response)
        log.status.Print(
            f"     Successfully created {resource_type_name}: {success_message}"
        )
  except (apitools_exceptions.HttpError, ValueError, NotImplementedError) as e:
    raise ValueError(
        f"Failed to deploy resource '{resource_id}' of type"
        f" '{resource_type_name}': {e}"
    ) from e
