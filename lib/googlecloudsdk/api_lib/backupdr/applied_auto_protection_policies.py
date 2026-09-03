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
"""Cloud AppliedAutoProtectionPolicies client."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.backupdr import util


class AppliedAutoProtectionPoliciesClient(util.BackupDrClientBase):
  """Cloud AppliedAutoProtectionPolicies client."""

  def __init__(self, api_version=util.DEFAULT_API_VERSION):
    super(AppliedAutoProtectionPoliciesClient, self).__init__(
        api_version=api_version
    )
    self.service = self.client.projects_locations_appliedAutoProtectionPolicies

  def List(self, location, limit=None, page_size=None):
    """List AppliedAutoProtectionPolicies in a given location."""
    request = self.messages.BackupdrProjectsLocationsAppliedAutoProtectionPoliciesListRequest(
        parent=location.RelativeName()
    )
    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size=page_size,
        limit=limit,
        field='appliedAutoProtectionPolicies',
        batch_size_attribute='pageSize',
    )
