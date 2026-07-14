# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Bigtable memory layers API helper."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import exceptions

MEMORY_LAYER_SUFFIX = '/memoryLayer'


def Describe(cluster_ref, client=None, msgs=None):
  """Describe a memory layer.

  Args:
    cluster_ref: A resource reference to the cluster of the memory layer to
      describe.
    client: The API client.
    msgs: The API messages.

  Returns:
    Memory layer resource object.
  """
  if client is None:
    client = util.GetAdminClient()
  if msgs is None:
    msgs = util.GetAdminMessages()
  memory_layer_name = cluster_ref.RelativeName() + MEMORY_LAYER_SUFFIX

  msg = msgs.BigtableadminProjectsInstancesClustersGetMemoryLayerRequest(
      name=memory_layer_name
  )
  return client.projects_instances_clusters.GetMemoryLayer(msg)


def List(
    cluster_ref=None, instance_ref=None, cluster=None, client=None, msgs=None
):
  """List memory layers.

  Args:
    cluster_ref: A resource reference to the cluster to list memory layers for.
    instance_ref: A resource reference to the instance to list memory layers
      for.
    cluster: string, The cluster ID if instance_ref is provided and cluster is
      specified.
    client: The API client.
    msgs: The API messages.

  Returns:
    Generator of memory layer resource objects.
  """
  if client is None:
    client = util.GetAdminClient()
  if msgs is None:
    msgs = util.GetAdminMessages()

  if cluster_ref:
    cluster_str = cluster_ref.RelativeName()
  elif instance_ref:
    if cluster:
      cluster_str = instance_ref.RelativeName() + '/clusters/' + cluster
    else:
      cluster_str = instance_ref.RelativeName() + '/clusters/-'
  else:
    raise exceptions.InvalidArgumentException(
        '--instance', '--instance must be specified'
    )

  msg = msgs.BigtableadminProjectsInstancesClustersMemoryLayersListRequest(
      parent=cluster_str
  )
  return list_pager.YieldFromList(
      client.projects_instances_clusters_memoryLayers,
      msg,
      field='memoryLayers',
      batch_size_attribute=None,
  )


def Update(
    cluster_ref,
    enable,
    client=None,
    msgs=None,
):
  """Update a memory layer.

  Args:
    cluster_ref: A resource reference to the cluster to update.
    enable: Whether to enable or disable the memory layer. If true, enable the
      memory layer. Otherwise, disable the memory layer.
    client: The API client.
    msgs: The API messages.

  Returns:
    Long running operation.
  """
  if client is None:
    client = util.GetAdminClient()
  if msgs is None:
    msgs = util.GetAdminMessages()
  memory_layer = msgs.MemoryLayer()
  if enable:
    memory_layer.memoryConfig = (
        msgs.GoogleBigtableAdminV2MemoryLayerMemoryConfig()
    )

  memory_layer_name = cluster_ref.RelativeName() + MEMORY_LAYER_SUFFIX

  msg = msgs.BigtableadminProjectsInstancesClustersUpdateMemoryLayerRequest(
      memoryLayer=memory_layer,
      name=memory_layer_name,
      updateMask='memory_config',
  )

  return client.projects_instances_clusters.UpdateMemoryLayer(msg)
