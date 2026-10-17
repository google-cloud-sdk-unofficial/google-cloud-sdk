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

from collections.abc import Sequence
from typing import Any

from apitools.base.py import encoding
from googlecloudsdk.api_lib.securesourcemanager import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages

VERSION_MAP = util.VERSION_MAP
GetClientInstance = util.GetClientInstance

# A comment accepted by BatchCreate: either a fully formed request message, a
# comment message, or a dict shaped like one of those two.
_CommentInput = (
    securesourcemanager_v1_messages.CreatePullRequestCommentRequest
    | securesourcemanager_v1_messages.PullRequestComment
    | dict[str, Any]
)

# A comment accepted by Resolve/Unresolve: either a comment resource reference
# or a comment ID to be parsed relative to the parent pull request.
_CommentRefOrId = resources.Resource | str


class PullRequestCommentsClient(util.SecureSourceManagerClientBase):
  """Client for Secure Source Manager pull request comments."""

  def __init__(self, location: str | None = None):
    super(PullRequestCommentsClient, self).__init__(
        base.ReleaseTrack.ALPHA, location=location
    )
    self._service = (
        self.client.projects_locations_repositories_pullRequests_pullRequestComments
    )

  def Create(
      self,
      pull_request_comment_ref: resources.Resource,
      body: str,
  ) -> securesourcemanager_v1_messages.Operation:
    """Create a pull request comment."""
    pull_request_comment = self.messages.PullRequestComment(
        comment=self.messages.Comment(body=body),
    )
    create_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsPullRequestCommentsCreateRequest(
        parent=pull_request_comment_ref.RelativeName(),
        pullRequestComment=pull_request_comment,
    )
    return self._service.Create(create_req)

  def _MakeCreateCommentRequest(
      self,
      pull_request_ref: resources.Resource,
      comment: _CommentInput,
  ) -> securesourcemanager_v1_messages.CreatePullRequestCommentRequest:
    """Normalizes one comment input into a CreatePullRequestCommentRequest.

    Args:
      pull_request_ref: the parent pull request resource reference.
      comment: a CreatePullRequestCommentRequest, a PullRequestComment, a dict
        of either shape.

    Returns:
      A CreatePullRequestCommentRequest with the parent populated.
    """
    parent = pull_request_ref.RelativeName()

    # Case 1: already a full request message; only backfill the parent.
    if isinstance(comment, self.messages.CreatePullRequestCommentRequest):
      comment.parent = comment.parent or parent
      return comment

    # Case 2: a comment message; wrap it in a request.
    if isinstance(comment, self.messages.PullRequestComment):
      return self.messages.CreatePullRequestCommentRequest(
          parent=parent,
          pullRequestComment=comment,
      )

    # Case 3: a dict shaped like a request; decode it and backfill the parent.
    if isinstance(comment, dict) and 'pullRequestComment' in comment:
      create_req = encoding.PyValueToMessage(
          self.messages.CreatePullRequestCommentRequest, comment
      )
      create_req.parent = create_req.parent or parent
      return create_req

    # Default: a dict shaped like a comment; decode and wrap it.
    return self.messages.CreatePullRequestCommentRequest(
        parent=parent,
        pullRequestComment=encoding.PyValueToMessage(
            self.messages.PullRequestComment, comment
        ),
    )

  def BatchCreate(
      self,
      pull_request_ref: resources.Resource,
      comments: Sequence[_CommentInput],
  ) -> securesourcemanager_v1_messages.Operation:
    """Batch create pull request comments."""
    requests = [
        self._MakeCreateCommentRequest(pull_request_ref, comment)
        for comment in comments
    ]

    batch_create_req_body = self.messages.BatchCreatePullRequestCommentsRequest(
        requests=requests,
    )
    batch_create_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsPullRequestCommentsBatchCreateRequest(
        parent=pull_request_ref.RelativeName(),
        batchCreatePullRequestCommentsRequest=batch_create_req_body,
    )
    return self._service.BatchCreate(batch_create_req)

  def Update(
      self,
      pull_request_comment_ref: resources.Resource,
      body: str | None = None,
      update_mask: str | list[str] | None = None,
  ) -> securesourcemanager_v1_messages.Operation:
    """Update a pull request comment."""
    pull_request_comment = self.messages.PullRequestComment(
        name=pull_request_comment_ref.RelativeName(),
        comment=self.messages.Comment(body=body),
    )
    update_mask_str = (
        ','.join(update_mask) if isinstance(update_mask, list) else update_mask
    )
    update_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsPullRequestCommentsPatchRequest(
        name=pull_request_comment_ref.RelativeName(),
        pullRequestComment=pull_request_comment,
        updateMask=update_mask_str,
    )
    return self._service.Patch(update_req)

  def Delete(
      self, pull_request_comment_ref: resources.Resource
  ) -> securesourcemanager_v1_messages.Operation:
    """Delete a pull request comment."""
    delete_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsPullRequestCommentsDeleteRequest(
        name=pull_request_comment_ref.RelativeName(),
    )
    return self._service.Delete(delete_req)

  def Resolve(
      self,
      pull_request_ref: resources.Resource,
      comments: Sequence[_CommentRefOrId],
      auto_fill: bool | None = None,
  ) -> securesourcemanager_v1_messages.Operation:
    """Resolve pull request comments."""
    comment_names = []
    for comment in comments:
      if isinstance(comment, resources.Resource):
        comment_names.append(comment.RelativeName())
      else:
        comment_ref = self._resource_parser.Parse(
            comment,
            params={
                'projectsId': pull_request_ref.projectsId,
                'locationsId': pull_request_ref.locationsId,
                'repositoriesId': pull_request_ref.repositoriesId,
                'pullRequestsId': pull_request_ref.pullRequestsId,
            },
            collection='securesourcemanager.projects.locations.repositories.pullRequests.pullRequestComments',
        )
        comment_names.append(comment_ref.RelativeName())

    resolve_req_body = self.messages.ResolvePullRequestCommentsRequest(
        names=comment_names,
        autoFill=auto_fill,
    )
    resolve_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsPullRequestCommentsResolveRequest(
        parent=pull_request_ref.RelativeName(),
        resolvePullRequestCommentsRequest=resolve_req_body,
    )
    return self._service.Resolve(resolve_req)

  def Unresolve(
      self,
      pull_request_ref: resources.Resource,
      comments: Sequence[_CommentRefOrId],
      auto_fill: bool | None = None,
  ) -> securesourcemanager_v1_messages.Operation:
    """Unresolve pull request comments."""
    comment_names = []
    for comment in comments:
      if isinstance(comment, resources.Resource):
        comment_names.append(comment.RelativeName())
      else:
        comment_ref = self._resource_parser.Parse(
            comment,
            params={
                'projectsId': pull_request_ref.projectsId,
                'locationsId': pull_request_ref.locationsId,
                'repositoriesId': pull_request_ref.repositoriesId,
                'pullRequestsId': pull_request_ref.pullRequestsId,
            },
            collection='securesourcemanager.projects.locations.repositories.pullRequests.pullRequestComments',
        )
        comment_names.append(comment_ref.RelativeName())

    unresolve_req_body = self.messages.UnresolvePullRequestCommentsRequest(
        names=comment_names,
        autoFill=auto_fill,
    )
    unresolve_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesPullRequestsPullRequestCommentsUnresolveRequest(
        parent=pull_request_ref.RelativeName(),
        unresolvePullRequestCommentsRequest=unresolve_req_body,
    )
    return self._service.Unresolve(unresolve_req)

