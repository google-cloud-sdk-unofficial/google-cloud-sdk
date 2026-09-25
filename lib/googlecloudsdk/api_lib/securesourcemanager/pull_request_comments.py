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
"""The Secure Source Manager pull request comments client module."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources

VERSION_MAP = {base.ReleaseTrack.ALPHA: 'v1'}


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA, location=None):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance(
      'securesourcemanager', api_version, location=location
  )


class PullRequestCommentsClient(object):
  """Client for Secure Source Manager pull request comments."""

  def __init__(self, location=None):
    self.client = GetClientInstance(base.ReleaseTrack.ALPHA, location=location)
    self.messages = self.client.MESSAGES_MODULE
    self._service = (
        self.client.projects_locations_repositories_pullRequests_pullRequestComments
    )
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName('securesourcemanager', 'v1')

  def Create(self, pull_request_comment_ref, body):
    """Create a pull request comment."""
    pull_request_comment = self.messages.PullRequestComment(
        comment=self.messages.Comment(body=body),
    )
    create_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsPullRequestCommentsCreateRequest(
        parent=pull_request_comment_ref.RelativeName(),
        pullRequestComment=pull_request_comment,
    )
    return self._service.Create(create_req)
