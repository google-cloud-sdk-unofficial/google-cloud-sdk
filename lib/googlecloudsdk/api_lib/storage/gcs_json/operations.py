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
"""API client for GCS long-running operations."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis as core_apis


class OperationsApi:
  """Client for GCS operations API (V2)."""

  def __init__(self):
    super(OperationsApi, self).__init__()
    self.client = core_apis.GetClientInstance("storage", "v2")
    self.messages = core_apis.GetMessagesModule("storage", "v2")

  def get(self, name):
    """Gets details of an operation."""
    request = self.messages.StorageProjectsLocationsOperationsGetRequest(
        name=name
    )
    return self.client.projects_locations_operations.Get(request)

  def cancel(self, name):
    """Cancels a running operation."""
    request = self.messages.StorageProjectsLocationsOperationsCancelRequest(
        name=name
    )
    return self.client.projects_locations_operations.Cancel(request)

  def list(self, name, server_side_filter=None):
    """Lists operations under a parent resource."""
    if name.endswith("/operations"):
      name = name[: -len("/operations")]
    request = self.messages.StorageProjectsLocationsOperationsListRequest(
        name=name, filter=server_side_filter
    )
    return list_pager.YieldFromList(
        self.client.projects_locations_operations,
        request,
        batch_size_attribute="pageSize",
        field="operations",
        current_token_attribute="pageToken",
        next_token_attribute="nextPageToken",
    )
