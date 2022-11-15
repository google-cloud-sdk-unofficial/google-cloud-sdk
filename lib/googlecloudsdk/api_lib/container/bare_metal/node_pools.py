
# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for node pool resources in Anthos clusters on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis


class NodePoolsClient(object):
  """Client for node pools in Anthos clusters on bare metal API."""

  def __init__(self, client=None, messages=None):
    self.client = client or apis.GetClientInstance('gkeonprem', 'v1')
    self.messages = messages or apis.GetMessagesModule('gkeonprem', 'v1')
    self._service = self.client.projects_locations_bareMetalClusters_bareMetalNodePools

  def List(self, location_ref, limit=None, page_size=None):
    """Lists Node Pools in the Anthos clusters on bare metal API."""
    list_req = self.messages.GkeonpremProjectsLocationsBareMetalClustersBareMetalNodePoolsListRequest(
        parent=location_ref.RelativeName())
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='bareMetalNodePools',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )
