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
"""Client for Secure Source Manager Pull Requests."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources

VERSION_MAP = {base.ReleaseTrack.ALPHA: "v1"}


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA, location=None):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance(
      "securesourcemanager", api_version, location=location
  )


class PullRequestsClient(object):
  """Client for Secure Source Manager Pull Requests."""

  def __init__(self, location=None):
    self.client = GetClientInstance(location=location)
    self.messages = self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_repositories_pullRequests
    self._resource_parser = resources.Registry()

  def Create(self, repository_ref, title, body, base_branch, head_branch):
    """Create a pull request."""
    parent = repository_ref.RelativeName()
    pull_request = self.messages.PullRequest(
        title=title,
        body=body,
        base=self.messages.Branch(ref=base_branch),
        head=self.messages.Branch(ref=head_branch),
    )
    create_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsCreateRequest(
        parent=parent,
        pullRequest=pull_request,
    )
    return self._service.Create(create_req)
