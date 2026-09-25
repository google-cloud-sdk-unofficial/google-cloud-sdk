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
"""Utilities for Assured Workloads API, Settings Endpoints."""

from typing import Any, Optional

from googlecloudsdk.api_lib.assured import util
from googlecloudsdk.calliope.base import ReleaseTrack


class SettingsClient:
  """Client for Organization Settings in Assured Workloads API."""

  def __init__(
      self,
      release_track: ReleaseTrack,
      no_http: bool = False,
      api_version: str = 'v2',
  ):
    """Initializes the Assured Workloads Settings client.

    Args:
      release_track: The release track for the CLI command.
      no_http: Whether to avoid making actual HTTP requests.
      api_version: The API version to use (defaults to 'v2').
    """
    self.client = util.GetClientInstance(
        release_track, no_http=no_http, api_version=api_version
    )
    self.messages = self.client.MESSAGES_MODULE
    self._release_track = release_track
    self._api_version = api_version
    self._service = self.client.organizations

  def Describe(self, name: str) -> Any:
    """Gets the AssuredWorkloadsSettings singleton resource for an organization.

    Args:
      name: The resource name in the form
        organizations/{ORG_ID}/assuredWorkloadsSettings.

    Returns:
      The AssuredWorkloadsSettings resource.
    """
    get_req = self.messages.AssuredworkloadsOrganizationsGetAssuredWorkloadsSettingsRequest(
        name=name
    )
    return self._service.GetAssuredWorkloadsSettings(get_req)

  def Update(self, settings: Any, update_mask: Optional[str] = None) -> Any:
    """Updates the AssuredWorkloadsSettings singleton resource for an organization.

    Args:
      settings: The settings resource with updated values.
      update_mask: Optional comma-separated list of fields to update (e.g.
        'olpc_mode').

    Returns:
      The updated AssuredWorkloadsSettings resource.
    """
    update_req = self.messages.AssuredworkloadsOrganizationsUpdateAssuredWorkloadsSettingsRequest(
        name=settings.name,
        googleCloudAssuredworkloadsV2AssuredWorkloadsSettings=settings,
        updateMask=update_mask,
    )
    return self._service.UpdateAssuredWorkloadsSettings(update_req)
