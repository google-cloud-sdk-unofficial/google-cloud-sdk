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
"""Domains client for App Topology API."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.app_topology import GetClientInstance
from googlecloudsdk.api_lib.app_topology import GetMessagesModule


class DomainsClient(object):
  """Client for interacting with the Domains resource."""

  def __init__(self, version='v1'):
    self.client = GetClientInstance(version)
    self.messages = GetMessagesModule(version)
    self._service = self.client.projects_locations_domains

  def List(self, parent, page_size=None, limit=None):
    """Lists topology domains in the specified parent location.

    Args:
      parent: str, Fully qualified location parent name (e.g.,
        'projects/{project}/locations/{location}').
      page_size: int or None, Maximum number of domains to return per batch.
      limit: int or None, Maximum total number of domains to yield.

    Returns:
      Generator: Yields Domain protobuf messages.
    """
    request = self.messages.ApptopologyProjectsLocationsDomainsListRequest(
        parent=parent
    )
    return list_pager.YieldFromList(
        self._service,
        request,
        field='domains',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def Get(self, name):
    """Retrieves metadata for a specific topology domain.

    Args:
      name: str, Fully qualified domain resource name (e.g.,
        'projects/{project}/locations/{location}/domains/{domain}').

    Returns:
      messages.Domain: The domain message.
    """
    request = self.messages.ApptopologyProjectsLocationsDomainsGetRequest(
        name=name
    )
    return self._service.Get(request)

  def GetSchema(self, name):
    """Retrieves the graph schema definition for the specified topology domain.

    Args:
      name: str, Fully qualified domain schema resource name (e.g.,
        'projects/{project}/locations/{location}/domains/{domain}/schema').

    Returns:
      messages.Schema: The schema definition message containing node and edge
      types.
    """
    request = self.messages.ApptopologyProjectsLocationsDomainsGetSchemaRequest(
        name=name
    )
    return self._service.GetSchema(request)
