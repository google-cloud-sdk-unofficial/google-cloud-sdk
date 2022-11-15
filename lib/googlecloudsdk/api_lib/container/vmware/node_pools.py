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
"""Utilities for node pool resources in Anthos clusters on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.vmware import client


class NodePoolsClient(client.ClientBase):
  """Client for node pools in Anthos clusters on VMware API."""

  def __init__(self, **kwargs):
    super(NodePoolsClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_vmwareClusters_vmwareNodePools

  def List(self, location_ref, limit=None, page_size=100):
    """Lists Node Pools in the Anthos clusters on VMware API."""
    list_req = self._messages.GkeonpremProjectsLocationsVmwareClustersVmwareNodePoolsListRequest(
        parent=location_ref.RelativeName())
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='vmwareNodePools',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def Delete(self,
             resource_ref,
             allow_missing=False,
             etag=None,
             validate_only=False):
    """Deletes a gkeonprem node pool API resource."""
    req = self._messages.GkeonpremProjectsLocationsVmwareClustersVmwareNodePoolsDeleteRequest(
        allowMissing=allow_missing,
        etag=etag,
        name=resource_ref.RelativeName(),
        validateOnly=validate_only)
    return self._service.Delete(req)

  def Create(
      self,
      resource_ref,
      image_type,
      replicas,
      enable_load_balancer,
      min_replicas=0,
      max_replicas=0,
      validate_only=False,
  ):
    """Creates a gkeonprem node pool API resource."""
    vmware_node_pool = self._messages.VmwareNodePool(
        name=resource_ref.RelativeName(),
        config=self._messages.VmwareNodeConfig(
            imageType=image_type,
            replicas=replicas,
            enableLoadBalancer=enable_load_balancer,
        ),
        nodePoolAutoscaling=self._messages.VmwareNodePoolAutoscalingConfig(
            minReplicas=min_replicas,
            maxReplicas=max_replicas,
        ))
    req = self._messages.GkeonpremProjectsLocationsVmwareClustersVmwareNodePoolsCreateRequest(
        parent=resource_ref.Parent().RelativeName(),
        validateOnly=validate_only,
        vmwareNodePool=vmware_node_pool,
        vmwareNodePoolId=resource_ref.Name(),
    )
    return self._service.Create(req)
