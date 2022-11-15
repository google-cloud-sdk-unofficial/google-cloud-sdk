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
"""Utilities for gkeonprem API clients for VMware admin cluster resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import client
from googlecloudsdk.api_lib.container.gkeonprem import update_mask
from googlecloudsdk.command_lib.container.vmware import flags


class AdminClustersClient(client.ClientBase):
  """Client for clusters in gkeonprem vmware API."""

  def __init__(self, **kwargs):
    super(AdminClustersClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_vmwareAdminClusters

  def Enroll(self, args):
    """Enrolls an admin cluster to Anthos on VMware."""
    kwargs = {
        'membership': self._admin_cluster_membership_name(args),
        'vmwareAdminClusterId': self._admin_cluster_id(args),
    }
    req = self._messages.GkeonpremProjectsLocationsVmwareAdminClustersEnrollRequest(
        parent=self._admin_cluster_parent(args),
        enrollVmwareAdminClusterRequest=self._messages
        .EnrollVmwareAdminClusterRequest(**kwargs),
    )
    return self._service.Enroll(req)

  def Update(self, args):
    """Updates an admin cluster to Anthos on VMware."""
    kwargs = {
        'name':
            self._admin_cluster_name(args),
        'updateMask':
            update_mask.get_update_mask(
                args, update_mask.VMWARE_ADMIN_CLUSTER_ARGS_TO_UPDATE_MASKS),
        'vmwareAdminCluster':
            self._vmware_admin_cluster(args),
    }
    req = self._messages.GkeonpremProjectsLocationsVmwareAdminClustersPatchRequest(
        **kwargs)
    return self._service.Patch(req)

  def _vmware_admin_cluster(self, args):
    """Constructs proto message VmwareAdminCluster."""
    kwargs = {
        'platformConfig': self._platform_config(args),
    }
    if any(kwargs.values()):
      return self._messages.VmwareAdminCluster(**kwargs)
    return None

  def _platform_config(self, args):
    """Constructs proto message field platform_config."""
    kwargs = {
        'requiredPlatformVersion': flags.Get(args, 'required_platform_version'),
    }
    if any(kwargs.values()):
      return self._messages.VmwarePlatformConfig(**kwargs)
    return None
