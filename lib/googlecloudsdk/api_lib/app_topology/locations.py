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
"""Locations client for App Topology API."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.app_topology import GetClientInstance
from googlecloudsdk.api_lib.app_topology import GetMessagesModule


class LocationsClient(object):
  """Client for interacting with the Locations resource."""

  def __init__(self, version='v1'):
    self.client = GetClientInstance(version)
    self.messages = GetMessagesModule(version)
    self._service = self.client.projects_locations

  def List(self, parent, page_size=None, limit=None, filter_str=None):
    """Lists available locations in the specified project.

    Args:
      parent: str, Fully qualified project name (e.g., 'projects/{project}').
      page_size: int or None, Maximum number of locations to return per batch.
      limit: int or None, Maximum total number of locations to yield.
      filter_str: str or None, Optional backend AIP-160 filter expression.

    Returns:
      Generator: Yields Location protobuf messages.
    """
    request = self.messages.ApptopologyProjectsLocationsListRequest(
        name=parent, filter=filter_str
    )
    return list_pager.YieldFromList(
        self._service,
        request,
        field='locations',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def Get(self, name):
    """Retrieves metadata for a specific location.

    Args:
      name: str, Fully qualified location resource name (e.g.,
        'projects/{project}/locations/{location}').

    Returns:
      messages.Location: The location message.
    """
    request = self.messages.ApptopologyProjectsLocationsGetRequest(name=name)
    return self._service.Get(request)
