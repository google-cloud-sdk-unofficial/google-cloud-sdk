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
"""The Secure Source Manager pull requests client module."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources

VERSION_MAP = {base.ReleaseTrack.ALPHA: 'v1'}


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA, location=None):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance(
      'securesourcemanager', api_version, location=location
  )


class PullRequestsClient(object):
  """Client for Secure Source Manager pull requests."""

  def __init__(self, location=None):
    self.client = GetClientInstance(base.ReleaseTrack.ALPHA, location=location)
    self.messages = self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_repositories_pullRequests
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName('securesourcemanager', 'v1')

  def Create(self, pull_request_ref, title, body, base_branch, head_branch):
    """Create a pull request."""
    pull_request = self.messages.PullRequest(
        title=title,
        body=body,
        base=self.messages.Branch(ref=base_branch),
        head=self.messages.Branch(ref=head_branch),
    )
    create_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsCreateRequest(
        parent=pull_request_ref.RelativeName(),
        pullRequest=pull_request,
    )
    return self._service.Create(create_req)

  def Update(self, pull_request_ref, title=None, body=None, update_mask=None):
    """Update a pull request."""
    name = pull_request_ref.RelativeName()
    pull_request = self.messages.PullRequest(name=name, title=title, body=body)
    update_mask_str = (
        ','.join(update_mask) if isinstance(update_mask, list) else update_mask
    )
    update_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsPatchRequest(
        name=pull_request_ref.RelativeName(),
        pullRequest=pull_request,
        updateMask=update_mask_str,
    )
    return self._service.Patch(update_req)

  def Merge(self, pull_request_ref):
    """Merge a pull request."""
    merge_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsMergeRequest(
        name=pull_request_ref.RelativeName(),
        mergePullRequestRequest=self.messages.MergePullRequestRequest(),
    )
    return self._service.Merge(merge_req)

  def Open(self, pull_request_ref):
    """Open a pull request."""
    open_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsOpenRequest(
        name=pull_request_ref.RelativeName(),
        openPullRequestRequest=self.messages.OpenPullRequestRequest(),
    )
    return self._service.Open(open_req)

  def Close(self, pull_request_ref):
    """Close a pull request."""
    close_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsCloseRequest(
        name=pull_request_ref.RelativeName(),
        closePullRequestRequest=self.messages.ClosePullRequestRequest(),
    )
    return self._service.Close(close_req)
