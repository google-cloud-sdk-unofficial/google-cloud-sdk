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
"""Utilities for querying Vertex AI Agent Runtimes.

The Agent Runtimes gcloud surface is backed by the ReasoningEngine API resource,
so all requests target the `reasoningEngines` collection.
"""

from __future__ import annotations

from typing import Any

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import constants


class AgentRuntimesClient:
  """Client used for interacting with the ReasoningEngine endpoint."""

  def __init__(self, version: str = constants.GA_VERSION) -> None:
    """Initializes the Agent Runtimes API client.

    Args:
      version: The API release track version (e.g. constants.GA_VERSION or
        constants.BETA_VERSION).
    """
    client = apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[version],
    )
    self._messages = client.MESSAGES_MODULE
    self._version = version
    self._service = client.projects_locations_reasoningEngines
    self._message_prefix = constants.AI_PLATFORM_MESSAGE_PREFIX[version]

  def GetMessage(self, message_name: str) -> Any:
    """Returns the API message class by name."""

    return getattr(
        self._messages,
        f'{self._message_prefix}{message_name}',
        None,
    )

  def _ReasoningEngineRequestField(self) -> str:
    """Returns the version-specific ReasoningEngine request body field name.

    The create and patch requests embed the ReasoningEngine resource in a field
    whose name depends on the API version (e.g.
    `googleCloudAiplatformV1ReasoningEngine` for GA and
    `googleCloudAiplatformV1beta1ReasoningEngine` for BETA). This derives that
    field name from the message prefix so callers stay version-agnostic.

    Returns:
      The request body field name for the ReasoningEngine resource.
    """
    lower_prefix = self._message_prefix[0].lower() + self._message_prefix[1:]
    return f'{lower_prefix}ReasoningEngine'

  def List(self, limit: int | None = None, region: str | None = None) -> Any:
    """Constructs a list request and sends it to the Agent Runtimes endpoint.

    Args:
      limit: How many items to return in the list.
      region: Which region to list resources from.

    Returns:
      An iterator yielding ReasoningEngine resources.
    """
    return list_pager.YieldFromList(
        self._service,
        self._messages.AiplatformProjectsLocationsReasoningEnginesListRequest(
            parent=region
        ),
        field='reasoningEngines',
        batch_size_attribute='pageSize',
        limit=limit,
    )

  def Get(self, name: str) -> Any:
    """Retrieves an Agent Runtime resource by name.

    Args:
      name: The Agent Runtime resource name, in the form
        `projects/{project}/locations/{location}/reasoningEngines/{reasoning_engine}`.

    Returns:
      The ReasoningEngine resource message.
    """
    request = (
        self._messages.AiplatformProjectsLocationsReasoningEnginesGetRequest(
            name=name
        )
    )
    return self._service.Get(request)

  def Delete(self, name: str, force: bool | None = None) -> Any:
    """Deletes an Agent Runtime resource by name.

    Args:
      name: The Agent Runtime resource name, in the form
        `projects/{project}/locations/{location}/reasoningEngines/{reasoning_engine}`.
      force: If True, any child resources (e.g. revisions) are also deleted.

    Returns:
      The long-running operation for the delete request.
    """
    kwargs = {'name': name}
    if force is not None:
      kwargs['force'] = force
    request = (
        self._messages.AiplatformProjectsLocationsReasoningEnginesDeleteRequest(
            **kwargs
        )
    )
    return self._service.Delete(request)

  def Create(self, parent: str, reasoning_engine: Any) -> Any:
    """Creates a new Agent Runtime under the given parent.

    Args:
      parent: The location resource name to create the Agent Runtime in, in the
        form `projects/{project}/locations/{location}`.
      reasoning_engine: The ReasoningEngine message describing the Agent Runtime
        to create (e.g. built via `GetMessage('ReasoningEngine')`).

    Returns:
      The long-running operation for the create request.
    """
    request = (
        self._messages.AiplatformProjectsLocationsReasoningEnginesCreateRequest(
            parent=parent,
            **{self._ReasoningEngineRequestField(): reasoning_engine},
        )
    )
    return self._service.Create(request)

  def Update(
      self, name: str, reasoning_engine: Any, update_mask: str | None = None
  ) -> Any:
    """Updates an existing Agent Runtime.

    Args:
      name: The Agent Runtime resource name, in the form
        `projects/{project}/locations/{location}/reasoningEngines/{reasoning_engine}`.
      reasoning_engine: The ReasoningEngine message with the fields to update.
      update_mask: Optional comma-separated list of fields to update. When
        unset, the server applies its default masking behavior.

    Returns:
      The long-running operation for the update request.
    """
    request = (
        self._messages.AiplatformProjectsLocationsReasoningEnginesPatchRequest(
            name=name,
            updateMask=update_mask,
            **{self._ReasoningEngineRequestField(): reasoning_engine},
        )
    )
    return self._service.Patch(request)
