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
"""The Secure Source Manager hooks client module."""

from collections.abc import Sequence

from googlecloudsdk.api_lib.securesourcemanager import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages


class HooksClient(util.SecureSourceManagerClientBase):
  """Client for Secure Source Manager hooks."""

  def __init__(
      self,
      release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
      location: str | None = None,
  ):
    super().__init__(release_track=release_track, location=location)
    self._service = self.client.projects_locations_repositories_hooks

  def Create(
      self,
      hook_ref: resources.Resource,
      target_uri: str,
      events: Sequence[str] | None = None,
      disabled: bool = False,
  ) -> securesourcemanager_v1_messages.Operation:
    """Create a hook."""
    events_enums = []
    if events is not None:
      for event in events:
        events_enums.append(
            self.messages.Hook.EventsValueListEntryValuesEnum(event)
        )
    hook = self.messages.Hook(
        targetUri=target_uri,
        events=events_enums,
        disabled=disabled,
    )
    create_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesHooksCreateRequest(
        parent=hook_ref.Parent().RelativeName(),
        hook=hook,
        hookId=hook_ref.hooksId,
    )
    return self._service.Create(create_req)

  def Delete(
      self, hook_ref: resources.Resource
  ) -> securesourcemanager_v1_messages.Operation:
    """Delete a hook."""
    delete_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesHooksDeleteRequest(
        name=hook_ref.RelativeName()
    )
    return self._service.Delete(delete_req)

  def Update(
      self,
      hook_ref: resources.Resource,
      target_uri: str | None = None,
      events: Sequence[str] | None = None,
      disabled: bool | None = None,
      update_mask: Sequence[str] | None = None,
  ) -> securesourcemanager_v1_messages.Operation:
    """Update a hook."""
    events_enums = []
    if events is not None:
      for event in events:
        events_enums.append(
            self.messages.Hook.EventsValueListEntryValuesEnum(event)
        )
    hook = self.messages.Hook(
        name=hook_ref.RelativeName(),
        targetUri=target_uri,
        events=events_enums,
        disabled=disabled,
    )
    update_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesHooksPatchRequest(
        name=hook_ref.RelativeName(),
        hook=hook,
        updateMask=','.join(update_mask) if update_mask else None,
    )
    return self._service.Patch(update_req)
