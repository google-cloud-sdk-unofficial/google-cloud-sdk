# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Cloud vmware Privateclouds client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util
from googlecloudsdk.api_lib.vmware.networks import NetworksClient


class PrivateCloudsClient(util.VmwareClientBase):
  """cloud vmware privateclouds client."""

  def __init__(self):
    super(PrivateCloudsClient, self).__init__()
    self.service = self.client.projects_locations_privateClouds
    self.networks_client = NetworksClient()

  def Get(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsGetRequest(
        name=resource.RelativeName())

    response = self.service.Get(request)
    return response

  def Create(self,
             resource,
             description=None,
             cluster_id=None,
             nodes_configs=None,
             network_cidr=None,
             vmware_engine_network_id=None):
    parent = resource.Parent().RelativeName()
    project = resource.Parent().Parent().Name()
    private_cloud_id = resource.Name()
    private_cloud = self.messages.PrivateCloud(description=description)

    ven = self.networks_client.GetByID(project, vmware_engine_network_id)
    network_config = self.messages.NetworkConfig(
        managementCidr=network_cidr, vmwareEngineNetwork=ven.name)

    management_cluster = self.messages.ManagementCluster(clusterId=cluster_id)
    management_cluster.nodeTypeConfigs = util.ConstructNodeParameterConfigMessage(
        self.messages.ManagementCluster.NodeTypeConfigsValue,
        self.messages.NodeTypeConfig, nodes_configs)

    private_cloud.managementCluster = management_cluster
    private_cloud.networkConfig = network_config
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsCreateRequest(
        parent=parent,
        privateCloudId=private_cloud_id,
        privateCloud=private_cloud)
    return self.service.Create(request)

  def Update(self,
             resource,
             description=None):
    private_cloud = self.Get(resource)
    update_mask = []
    if description is not None:
      private_cloud.description = description
      update_mask.append('description')
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsPatchRequest(
        privateCloud=private_cloud,
        name=resource.RelativeName(),
        updateMask=','.join(update_mask))
    return self.service.Patch(request)

  def UnDelete(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsUndeleteRequest(
        name=resource.RelativeName())
    return self.service.Undelete(request)

  def Delete(self, resource, delay_hours=None):
    return self.service.Delete(
        self.messages.VmwareengineProjectsLocationsPrivateCloudsDeleteRequest(
            name=resource.RelativeName(), delayHours=delay_hours))

  def List(self,
           location_resource,
           filter_expression=None,
           limit=None,
           page_size=None,
           sort_by=None):
    location = location_resource.RelativeName()
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsListRequest(
        parent=location, filter=filter_expression)
    if page_size:
      request.page_size = page_size
    return list_pager.YieldFromList(
        self.service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='privateClouds')

  def GetNsxCredentials(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsShowNsxCredentialsRequest(
        privateCloud=resource.RelativeName())
    return self.service.ShowNsxCredentials(request)

  def ResetNsxCredentials(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsResetNsxCredentialsRequest(
        privateCloud=resource.RelativeName())
    return self.service.ResetNsxCredentials(request)

  def GetVcenterCredentials(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsShowVcenterCredentialsRequest(
        privateCloud=resource.RelativeName())
    return self.service.ShowVcenterCredentials(request)

  def ResetVcenterCredentials(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsResetVcenterCredentialsRequest(
        privateCloud=resource.RelativeName())
    return self.service.ResetVcenterCredentials(request)
