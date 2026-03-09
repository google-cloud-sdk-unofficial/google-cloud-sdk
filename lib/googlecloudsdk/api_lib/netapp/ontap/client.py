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

"""Commands for interacting with the Cloud NetApp Volumes ONTAP API."""

import json
from typing import Any

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.netapp import util as netapp_api_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exceptions
from googlecloudsdk.api_lib.util import messages as api_messages
from googlecloudsdk.calliope import base

ontap_api_path = "api/private/cli"


def _build_ontap_path(storage_pool_ref) -> str:
  """Builds the path for the ONTAP API request."""
  return f"{storage_pool_ref.RelativeName()}/ontap/{ontap_api_path}"


class OntapClient(object):
  """A client for working with ONTAP-mode APIs for Cloud NetApp Volumes."""

  def __init__(self, release_track: base.ReleaseTrack):
    self.release_track = release_track
    if self.release_track == base.ReleaseTrack.ALPHA:
      self._adapter = AlphaOntapAdapter(
          client=netapp_api_util.GetClientInstance(
              release_track=self.release_track
          ),
          messages=netapp_api_util.GetMessagesModule(
              release_track=self.release_track
          ),
      )
    elif self.release_track == base.ReleaseTrack.BETA:
      self._adapter = BetaOntapAdapter(
          client=netapp_api_util.GetClientInstance(
              release_track=self.release_track
          ),
          messages=netapp_api_util.GetMessagesModule(
              release_track=self.release_track
          ),
      )
    else:
      raise ValueError(
          f"[{netapp_api_util.VERSION_MAP[release_track]}] is not a valid API"
          " version."
      )

  @property
  def client(self):
    return self._adapter.client

  @property
  def messages(self):
    return self._adapter.messages

  def _parse_exception(self, e: apitools_exceptions.HttpError):
    """Parses an HttpError to extract a user-friendly error message.

    The ONTAP API often embeds a more specific JSON error message within the
    outer error message. This method attempts to extract that message.

    Args:
      e: The apitools_exceptions.HttpError object.

    Returns:
      A string containing the parsed error message, or a default message if
      parsing fails.
    """
    content = json.loads(e.content)
    error_message = content.get("error", {}).get("message", "")

    if not isinstance(error_message, str):
      return "Invalid ONTAP CLI command options provided."

    json_start_index = error_message.rfind("{")
    if json_start_index == -1:
      return "Invalid ONTAP CLI command options provided."

    nested_json_str = error_message[json_start_index:]
    try:
      nested_data = json.loads(nested_json_str)
      ontap_error_message = nested_data.get("message")
      if ontap_error_message:
        return ontap_error_message
      return "Invalid ONTAP CLI command options provided."
    except json.JSONDecodeError:
      return "Failed to parse nested error details from API response."

  def execute_ontap_post(self, storage_pool_ref: Any, config: str):
    """Executes a ONTAP-mode POST API request.

    Args:
      storage_pool_ref: The resource reference to the storage pool.
      config: A string representing the ONTAP CLI command.

    Returns:
      The body of the API response from the ONTAP API.

    Raises:
      gcloud_exceptions.HttpException: If an error occurs during the conversion
        of the request body to the API message format.
    """
    messages = self.messages
    body_dict = {"input": config}

    # Convert the Python dictionary to the BodyValue message type.
    try:
      body_value_message = api_messages.DictToMessageWithErrorCheck(
          body_dict, messages.ExecuteOntapPostRequest.BodyValue
      )
    except Exception as e:
      raise gcloud_exceptions.HttpException(
          "Failed to convert body to API message."
      ) from e

    post_request = self.messages.ExecuteOntapPostRequest(
        body=body_value_message
    )

    request = self.messages.NetappProjectsLocationsStoragePoolsOntapExecuteOntapPostRequest(
        executeOntapPostRequest=post_request,
        ontapPath=_build_ontap_path(storage_pool_ref),
    )

    try:
      response = (
          self.client.projects_locations_storagePools_ontap.ExecuteOntapPost(
              request
          )
      )
      return response.body
    except apitools_exceptions.HttpError as e:
      error_message = self._parse_exception(e)
      raise gcloud_exceptions.HttpException(error_message)


class AlphaOntapAdapter(object):
  """Adapter for alpha ONTAP-mode APIs for Cloud NetApp Volumes."""

  def __init__(self, client, messages):
    self.release_track = base.ReleaseTrack.ALPHA
    self.client = client
    self.messages = messages


class BetaOntapAdapter(AlphaOntapAdapter):
  """Adapter for Beta ONTAP-mode APIs for Cloud NetApp Volumes."""

  def __init__(self, client, messages):
    super(BetaOntapAdapter, self).__init__(client, messages)
    self.release_track = base.ReleaseTrack.BETA
    self.client = client
    self.messages = messages
