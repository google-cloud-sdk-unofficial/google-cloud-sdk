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
"""The Secure Source Manager branch rules client module."""

from collections.abc import Sequence

from apitools.base.protorpclite import messages as protorpc_messages
from googlecloudsdk.api_lib.securesourcemanager import util
from googlecloudsdk.core import resources


class BranchRulesClient(util.SecureSourceManagerClientBase):
  """Client for Secure Source Manager branch rules."""

  def __init__(self, location: str | None = None) -> None:
    super().__init__(location=location)
    self._service = self.client.projects_locations_repositories_branchRules

  def Create(
      self,
      branch_rule_ref: resources.Resource,
      include_pattern: str,
      minimum_approvals_count: int | None = None,
      minimum_reviews_count: int | None = None,
      require_pull_request: bool = False,
      require_comments_resolved: bool = False,
      require_code_owner_approval: bool = False,
      require_linear_history: bool = False,
      allow_stale_reviews: bool = False,
      disabled: bool = False,
  ) -> protorpc_messages.Message:
    """Creates a branch rule."""
    branch_rule = self.messages.BranchRule(
        includePattern=include_pattern,
        minimumApprovalsCount=minimum_approvals_count,
        minimumReviewsCount=minimum_reviews_count,
        requirePullRequest=require_pull_request,
        requireCommentsResolved=require_comments_resolved,
        requireCodeOwnerApproval=require_code_owner_approval,
        requireLinearHistory=require_linear_history,
        allowStaleReviews=allow_stale_reviews,
        disabled=disabled,
    )
    create_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesBranchRulesCreateRequest(
        parent=branch_rule_ref.Parent().RelativeName(),
        branchRule=branch_rule,
        branchRuleId=branch_rule_ref.branchRulesId,
    )
    return self._service.Create(create_req)

  def Delete(
      self, branch_rule_ref: resources.Resource
  ) -> protorpc_messages.Message:
    """Deletes a branch rule."""
    delete_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesBranchRulesDeleteRequest(
        name=branch_rule_ref.RelativeName()
    )
    return self._service.Delete(delete_req)

  def Update(
      self,
      branch_rule_ref: resources.Resource,
      include_pattern: str | None = None,
      minimum_approvals_count: int | None = None,
      minimum_reviews_count: int | None = None,
      require_pull_request: bool | None = None,
      require_comments_resolved: bool | None = None,
      require_code_owner_approval: bool | None = None,
      require_linear_history: bool | None = None,
      allow_stale_reviews: bool | None = None,
      disabled: bool | None = None,
      update_mask: Sequence[str] | None = None,
  ) -> protorpc_messages.Message:
    """Updates a branch rule."""
    branch_rule = self.messages.BranchRule(
        name=branch_rule_ref.RelativeName(),
        includePattern=include_pattern,
        minimumApprovalsCount=minimum_approvals_count,
        minimumReviewsCount=minimum_reviews_count,
        requirePullRequest=require_pull_request,
        requireCommentsResolved=require_comments_resolved,
        requireCodeOwnerApproval=require_code_owner_approval,
        requireLinearHistory=require_linear_history,
        allowStaleReviews=allow_stale_reviews,
        disabled=disabled,
    )
    update_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesBranchRulesPatchRequest(
        name=branch_rule_ref.RelativeName(),
        branchRule=branch_rule,
        updateMask=','.join(update_mask) if update_mask else None,
    )
    return self._service.Patch(update_req)
