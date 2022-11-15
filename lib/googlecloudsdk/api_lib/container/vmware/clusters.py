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
"""Utilities for gkeonprem API clients for VMware cluster resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.vmware import client


class ClustersClient(client.ClientBase):
  """Client for clusters in gkeonprem vmware API."""

  def __init__(self, **kwargs):
    super(ClustersClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_vmwareClusters

  def List(self, location_ref, limit=None, page_size=100):
    """Lists Clusters in the GKE On-Prem VMware API."""
    list_req = self._messages.GkeonpremProjectsLocationsVmwareClustersListRequest(
        parent=location_ref.RelativeName())
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='vmwareClusters',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize')

  def Enroll(self, admin_cluster_membership_ref, resource_ref, local_name=None):
    """Enrolls a VMware cluster to Anthos."""
    enroll_vmware_cluster_request = self._messages.EnrollVmwareClusterRequest(
        adminClusterMembership=admin_cluster_membership_ref.RelativeName(),
        vmwareClusterId=resource_ref.Name(),
        localName=local_name,
    )
    req = self._messages.GkeonpremProjectsLocationsVmwareClustersEnrollRequest(
        parent=resource_ref.Parent().RelativeName(),
        enrollVmwareClusterRequest=enroll_vmware_cluster_request,
    )
    return self._service.Enroll(req)

  def Unenroll(self, resource_ref, force=False):
    """Unenrolls an Anthos cluster on VMware."""
    req = (
        self._messages.GkeonpremProjectsLocationsVmwareClustersUnenrollRequest(
            name=resource_ref.RelativeName(),
            force=force,
        ))
    return self._service.Unenroll(req)

  def Delete(self,
             resource_ref,
             allow_missing=False,
             validate_only=False,
             force=False):
    """Deletes an Anthos cluster on VMware."""
    req = self._messages.GkeonpremProjectsLocationsVmwareClustersDeleteRequest(
        name=resource_ref.RelativeName(),
        allowMissing=allow_missing,
        validateOnly=validate_only,
        force=force,
    )
    return self._service.Delete(req)

  def Create(self, args, user_cluster_ref, admin_cluster_ref):
    """Creates an Anthos cluster on VMware."""
    req = self._messages.GkeonpremProjectsLocationsVmwareClustersCreateRequest(
        parent=user_cluster_ref.Parent().RelativeName(),
        validateOnly=args.validate_only,
        vmwareCluster=self._vmware_cluster(args, user_cluster_ref,
                                           admin_cluster_ref),
        vmwareClusterId=user_cluster_ref.Name(),
    )
    return self._service.Create(req)

  def _vmware_cluster(self, args, user_cluster_ref, admin_cluster_ref):
    """Constructs proto message field vmware_cluster."""
    return self._messages.VmwareCluster(
        name=user_cluster_ref.RelativeName(),
        adminClusterMembership=admin_cluster_ref.RelativeName(),
        onPremVersion=args.version,
        networkConfig=self._messages.VmwareNetworkConfig(
            serviceAddressCidrBlocks=args.service_address_cidr_blocks,
            podAddressCidrBlocks=args.pod_address_cidr_blocks,
        ),
        loadBalancer=self._load_balancer(args),
    )

  def _load_balancer(self, args):
    """Constructs proto message field load_balancer."""
    kwargs = {
        'f5Config': self._f5_config(args),
        'metalLbConfig': self._metal_lb_config(args),
        'vipConfig': self._vip_config(args),
    }
    if any(kwargs.values()):
      return self._messages.VmwareLoadBalancerConfig(**kwargs)
    return None

  def _vip_config(self, args):
    """Constructs proto message field vip_config."""
    kwargs = {
        'controlPlaneVip': args.control_plane_vip,
        'ingressVip': args.ingress_vip,
    }
    if any(kwargs.values()):
      return self._messages.VmwareVipConfig(**kwargs)
    return None

  def _f5_config(self, args):
    """Constructs proto message field f5_config."""
    kwargs = {
        'address': args.f5_config_address,
        'partition': args.f5_config_partition,
        'snatPool': args.f5_config_snat_pool,
    }
    if any(kwargs.values()):
      return self._messages.VmwareF5BigIpConfig(**kwargs)
    return None

  def _metal_lb_config(self, args):
    """Constructs proto message field metal_lb_config."""
    kwargs = {
        'addressPools': self._address_pools(args),
    }
    if any(kwargs.values()):
      return self._messages.VmwareMetalLbConfig(**kwargs)
    return None

  def _address_pools(self, args):
    """Constructs proto message field address_pools."""
    address_pools = []
    if args.metal_lb_config_address_pools:
      for address_pool in args.metal_lb_config_address_pools:
        address_pools.append(self._address_pool(address_pool))
    return address_pools

  def _address_pool(self, address_pool_args):
    """Constructs proto message field address_pool."""
    kwargs = {
        'addresses': address_pool_args.get('addresses', []),
        'avoidBuggyIps': address_pool_args.get('avoid_buggy_ips', False),
        'manualAssign': address_pool_args.get('manual_assign', False),
        'pool': address_pool_args.get('pool', ''),
    }
    if any(kwargs.values()):
      return self._messages.VmwareAddressPool(**kwargs)
    return None
