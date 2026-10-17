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
"""The Secure Source Manager issues client module."""

from collections.abc import Sequence

from googlecloudsdk.api_lib.securesourcemanager import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages


class IssuesClient(util.SecureSourceManagerClientBase):
  """Client for Secure Source Manager issues."""

  def __init__(
      self,
      release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
      location: str | None = None,
  ):
    super().__init__(release_track=release_track, location=location)
    self._service = self.client.projects_locations_repositories_issues

  def Create(
      self,
      issue_ref: resources.Resource,
      title: str,
      body: str | None,
  ) -> securesourcemanager_v1_messages.Operation:
    """Create an issue."""
    issue = self.messages.Issue(
        title=title,
        body=body,
    )
    create_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesIssuesCreateRequest(
        parent=issue_ref.RelativeName(),
        issue=issue,
    )
    return self._service.Create(create_req)

  def Delete(
      self, issue_ref: resources.Resource
  ) -> securesourcemanager_v1_messages.Operation:
    """Delete an issue."""
    delete_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesIssuesDeleteRequest(
        name=issue_ref.RelativeName()
    )
    return self._service.Delete(delete_req)

  def Update(
      self,
      issue_ref: resources.Resource,
      title: str | None = None,
      body: str | None = None,
      update_mask: Sequence[str] | None = None,
  ) -> securesourcemanager_v1_messages.Operation:
    """Update an issue."""
    issue = self.messages.Issue(
        name=issue_ref.RelativeName(),
        title=title,
        body=body,
    )
    update_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesIssuesPatchRequest(
        name=issue_ref.RelativeName(),
        issue=issue,
        updateMask=','.join(update_mask) if update_mask else None,
    )
    return self._service.Patch(update_req)

  def Open(
      self,
      issue_ref: resources.Resource,
      etag: str | None = None,
  ) -> securesourcemanager_v1_messages.Operation:
    """Open an issue."""
    open_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesIssuesOpenRequest(
        name=issue_ref.RelativeName(),
        openIssueRequest=self.messages.OpenIssueRequest(etag=etag),
    )
    return self._service.Open(open_req)

  def Close(
      self,
      issue_ref: resources.Resource,
      etag: str | None = None,
  ) -> securesourcemanager_v1_messages.Operation:
    """Close an issue."""
    close_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesIssuesCloseRequest(
        name=issue_ref.RelativeName(),
        closeIssueRequest=self.messages.CloseIssueRequest(etag=etag),
    )
    return self._service.Close(close_req)
