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
"""Orchestrator configuration utilities for clusters command group."""

from __future__ import annotations

import collections
from collections.abc import Mapping
import enum
import os
import re
from typing import Any

from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.cluster_director.clusters import errors
from googlecloudsdk.core.util import files

ClusterDirectorError = errors.ClusterDirectorError

_GCE_INSTANCE_FIELDS = frozenset([
    "startupScript",
    "labels",
    "bootDisk",
    "startupScriptTimeout",
])
_GKE_NODE_POOL_FIELDS = frozenset([
    "container-resource-labels",
    "container-startup-script",
])

# Error messages
_GCE_FIELDS_ON_GKE_NODE_SET_ERROR = (
    "GCE node set fields (startupScript, labels, bootDisk, "
    "startupScriptTimeout) cannot be specified for GKE node sets."
)
_GKE_FIELDS_ON_GCE_NODE_SET_ERROR = (
    "GKE node set fields (container-*) cannot be specified for GCE node sets."
)
_SLURM_NODESET_ALREADY_EXISTS_ERROR = (
    "Slurm nodesets with id={0} already exist."
)
_SLURM_NODESET_NOT_FOUND_ERROR = "Slurm nodesets with id={0} not found."
_SLURM_PARTITION_ALREADY_EXISTS_ERROR = (
    "Slurm partitions with id={0} already exist."
)
_SLURM_PARTITION_NOT_FOUND_ERROR = "Slurm partitions with id={0} not found."
_UPDATE_GCE_FIELDS_ON_GKE_NODE_SET_ERROR = (
    "Cannot update compute instance fields for a GKE node set."
)
_UPDATE_GKE_FIELDS_ON_GCE_NODE_SET_ERROR = (
    "Cannot update GKE node set fields for a compute instance node set."
)


class NodeSetType(enum.Enum):
  """Represents the type of a Slurm Node Set."""

  GCE = "gce"
  GKE = "gke"


def _ConvertMessageToDict(message) -> dict[str, Any]:
  """Convert a message with list of type AdditionalProperty(key=str, value=Any) to a dict."""
  if not message:
    return {}
  return {each.key: each.value for each in message.additionalProperties}


def _ConvertSlurmMessageToDict(message):
  """Convert a list of slurm message (SlurmNodeSet, SlurmPartition) to a dict."""
  if not message:
    return {}
  return {each.id: each for each in message}


def _AddKeyToDictSpec(
    key: str,
    dict_spec: dict[str, Any],
    value: Any,
    exception_message: str,
) -> None:
  """Adds a cluster identifier (key) with value, if not present in dict spec."""
  if key in dict_spec:
    raise ClusterDirectorError(exception_message.format(key))
  dict_spec[key] = value


def _RemoveKeyFromDictSpec(
    key: str, dict_spec: dict[str, Any], exception_message: str
) -> None:
  """Removes a cluster identifier (key), if present in dict spec."""
  if key not in dict_spec:
    raise ClusterDirectorError(exception_message.format(key))
  dict_spec.pop(key)


def _GetValueFromDictSpec(
    key: str, dict_spec: Mapping[str, Any], exception_message: str
) -> Any:
  """Returns the value message by cluster identifier (key) from a dict spec."""
  if key not in dict_spec:
    raise ClusterDirectorError(exception_message.format(key))
  return dict_spec[key]


def _CheckIfBashFileFormat(arg_value: str) -> bool:
  """Checks if the argument is a bash file format."""
  return bool(re.match(r"^\S*\.(sh|bash)$", arg_value))


def _GetBashScript(arg_value: str) -> str | exceptions.BadFileException:
  """Returns the bash script if argument is a valid bash file path."""
  if not arg_value or not _CheckIfBashFileFormat(arg_value):
    return arg_value
  path = arg_value
  if not os.path.isabs(path):
    raise exceptions.BadFileException(
        f"Script file path must be absolute, got {path}"
    )
  if not os.path.exists(path) or not os.path.isfile(path):
    raise exceptions.BadFileException(
        f"Script file not found at absolute path={path}"
    )
  return files.ReadFileContents(path)


def MakeLabels(label_args, label_cls):
  """Returns the labels message."""
  if not label_args:
    return None
  return label_cls(
      additionalProperties=[
          label_cls.AdditionalProperty(key=key, value=value)
          for key, value in sorted(label_args.items())
      ]
  )


def _GetStorageConfigs(message_module, cluster):
  """Returns the storage configs."""
  storage_configs: list[Any] = []
  if not cluster.storageResources:
    return storage_configs
  sorted_storages = sorted(
      cluster.storageResources.additionalProperties,
      key=lambda storage: storage.key,
  )
  if sorted_storages:
    first_storage = sorted_storages[0]
    storage_configs.append(
        message_module.StorageConfig(
            id=first_storage.key,
            localMount="/home",
        )
    )
  counters = collections.defaultdict(int)
  for storage in sorted_storages[1:]:
    local_mount = None
    if storage.value:
      if (
          storage.value.config.newFilestore
          or storage.value.config.existingFilestore
      ):
        local_mount = f"/shared{counters['filestore']}"
        counters["filestore"] += 1
      elif (
          storage.value.config.newLustre or storage.value.config.existingLustre
      ):
        local_mount = f"/scratch{counters['lustre']}"
        counters["lustre"] += 1
      elif (
          storage.value.config.newBucket
          or storage.value.config.existingBucket
      ):
        local_mount = f"/data{counters['bucket']}"
        counters["bucket"] += 1
    if not local_mount:
      raise ClusterDirectorError("Storage configuration is not supported.")

    storage_configs.append(
        message_module.StorageConfig(
            id=storage.key,
            localMount=local_mount,
        )
    )
  return storage_configs


def _GetComputeMachineType(
    compute_id: str, compute_resources: dict[str, Any]
) -> Any:
  """Returns the compute machine type from compute resources."""
  compute_resource = compute_resources[compute_id]
  if compute_resource.config.newOnDemandInstances:
    return compute_resource.config.newOnDemandInstances.machineType
  if compute_resource.config.newSpotInstances:
    return compute_resource.config.newSpotInstances.machineType
  if compute_resource.config.newReservedInstances:
    return compute_resource.config.newReservedInstances.machineType
  if compute_resource.config.newFlexStartInstances:
    return compute_resource.config.newFlexStartInstances.machineType
  raise ClusterDirectorError("Compute instances type not supported.")


def _GetComputeMachineTypeFromCluster(
    compute_id: str, cluster, existing_cluster=None, use_existing_cluster=False
) -> Any:
  """Returns the compute machine type from cluster."""
  if cluster:
    compute_resources = _ConvertMessageToDict(cluster.computeResources)
    if compute_id in compute_resources:
      return _GetComputeMachineType(compute_id, compute_resources)
  if use_existing_cluster and existing_cluster:
    compute_resources = _ConvertMessageToDict(existing_cluster.computeResources)
    if compute_id in compute_resources:
      return _GetComputeMachineType(compute_id, compute_resources)
  raise ClusterDirectorError(
      f"Compute instances with id={compute_id} not found."
  )


def _GetComputeMachineTypeFromArgs(args, compute_id):
  """Returns the compute machine type from args."""
  instances = []
  if args.IsSpecified("on_demand_instances"):
    instances.extend(args.on_demand_instances)
  if args.IsSpecified("spot_instances"):
    instances.extend(args.spot_instances)
  if args.IsSpecified("reserved_instances"):
    instances.extend(args.reserved_instances)
  if args.IsSpecified("flex_start_instances"):
    instances.extend(args.flex_start_instances)
  for instance in instances:
    if instance.get("id") == compute_id:
      return instance.get("machineType")
  raise ClusterDirectorError(
      f"Compute instances with id={compute_id} not found."
  )


def _MakeSlurmPartition(message_module, partition):
  """Makes a cluster slurm partition message from partition args."""
  slurm_partition = message_module.SlurmPartition(
      id=partition.get("id"),
      nodeSetIds=partition.get("nodeSetIds"),
  )
  if hasattr(slurm_partition, "exclusive"):
    slurm_partition.exclusive = partition.get("exclusive")
  return slurm_partition


def _MakeSlurmNodeSet(message_module, node_set, storage_configs):
  """Makes a cluster slurm node set message from node set args."""
  node_set_keys = set(node_set.keys())
  node_set_type_str = node_set.get("type")
  has_gke_fields = node_set_keys.intersection(_GKE_NODE_POOL_FIELDS)
  has_gce_fields = node_set_keys.intersection(_GCE_INSTANCE_FIELDS)

  node_set_type = None
  if node_set_type_str:
    try:
      node_set_type = NodeSetType(node_set_type_str)
    except ValueError as exc:
      raise ClusterDirectorError(
          f"Invalid node set type: {node_set_type_str!r}. "
          "Must be 'gce' or 'gke'."
      ) from exc

  is_container_node_pool = node_set_type == NodeSetType.GKE or (
      node_set_type is None and has_gke_fields
  )
  if is_container_node_pool and has_gce_fields:
    raise ClusterDirectorError(_GCE_FIELDS_ON_GKE_NODE_SET_ERROR)
  if not is_container_node_pool and has_gke_fields:
    raise ClusterDirectorError(_GKE_FIELDS_ON_GCE_NODE_SET_ERROR)
  slurm_node_set = message_module.SlurmNodeSet(
      id=node_set.get("id"),
      staticNodeCount=node_set.get("staticNodeCount", 1),
      maxDynamicNodeCount=node_set.get("maxDynamicNodeCount"),
      storageConfigs=storage_configs,
      computeId=node_set.get("computeId"),
  )
  if is_container_node_pool:
    if not hasattr(slurm_node_set, "containerNodePool"):
      raise ClusterDirectorError(
          "GKE node set fields (container-*) are not supported in this API "
          "version."
      )
    slurm_node_set.containerNodePool = (
        message_module.ContainerNodePoolSlurmNodeSet(
            resourceLabels=MakeLabels(
                label_args=node_set.get("container-resource-labels"),
                label_cls=(
                    message_module.ContainerNodePoolSlurmNodeSet
                    .ResourceLabelsValue
                ),
            ),
            startupScript=_GetBashScript(
                node_set.get("container-startup-script")
            ),
        )
    )
  else:
    if not node_set.get("computeId"):
      raise ClusterDirectorError(
          "computeId is required for node sets not backed by GKE."
      )
    conf = node_set.get("computeInstance") or node_set
    startup_script = _GetBashScript(conf.get("startupScript"))
    compute_instance_labels = MakeLabels(
        label_args=conf.get("labels"),
        label_cls=message_module.ComputeInstanceSlurmNodeSet.LabelsValue,
    )
    boot_disk = conf.get("bootDisk")
    compute_instance_boot_disk = None
    if boot_disk:
      compute_instance_boot_disk = message_module.BootDisk(
          type=boot_disk.get("type"),
          sizeGb=boot_disk.get("sizeGb", 100),
      )
      if compute_instance_boot_disk and hasattr(
          compute_instance_boot_disk, "image"
      ):
        compute_instance_boot_disk.image = boot_disk.get("image")
    compute_instance = message_module.ComputeInstanceSlurmNodeSet(
        bootDisk=compute_instance_boot_disk,
        startupScript=startup_script,
        labels=compute_instance_labels,
    )
    if node_set.get("startupScriptTimeout"):
      compute_instance.startupScriptTimeout = node_set.get(
          "startupScriptTimeout")
    if hasattr(slurm_node_set, "computeId"):
      slurm_node_set.computeId = node_set.get("computeId")
    slurm_node_set.computeInstance = compute_instance

  return slurm_node_set


def MakeClusterSlurmOrchestrator(args, message_module, cluster):
  """Makes a cluster message with slurm orchestrator fields."""
  slurm = message_module.SlurmOrchestrator()
  default_storage_configs = _GetStorageConfigs(message_module, cluster)
  if args.IsSpecified("slurm_node_sets"):
    for node_set in args.slurm_node_sets:
      node_set_keys = set(node_set.keys())
      node_set_type = node_set.get("type")
      has_gke_fields = node_set_keys.intersection(_GKE_NODE_POOL_FIELDS)
      is_gke = node_set_type == NodeSetType.GKE.value or (
          node_set_type is None and has_gke_fields
      )
      if not is_gke:
        compute_id = node_set.get("computeId")
        if compute_id:
          _GetComputeMachineTypeFromArgs(args, compute_id)
      storage_configs = default_storage_configs
      slurm.nodeSets.append(
          _MakeSlurmNodeSet(message_module, node_set, storage_configs)
      )

  if args.IsSpecified("slurm_partitions"):
    for partition in args.slurm_partitions:
      slurm.partitions.append(_MakeSlurmPartition(message_module, partition))

  if args.IsSpecified("slurm_default_partition"):
    slurm.defaultPartition = args.slurm_default_partition

  if args.IsSpecified("slurm_login_node"):
    login_node = args.slurm_login_node
    machine_type = login_node.get("machineType")
    storage_configs = default_storage_configs
    slurm.loginNodes = message_module.SlurmLoginNodes(
        count=login_node.get("count", 1),
        machineType=machine_type,
        zone=login_node.get("zone"),
        storageConfigs=storage_configs,
        enableOsLogin=login_node.get("enableOsLogin", True),
        enablePublicIps=login_node.get("enablePublicIps", True),
        startupScript=_GetBashScript(login_node.get("startupScript")),
        labels=MakeLabels(
            label_args=login_node.get("labels"),
            label_cls=message_module.SlurmLoginNodes.LabelsValue,
        ),
    )
    boot_disk_args = login_node.get("bootDisk")
    if boot_disk_args:
      boot_disk = message_module.BootDisk(
          type=boot_disk_args.get("type"),
          sizeGb=boot_disk_args.get("sizeGb", 100),
      )
      if hasattr(boot_disk, "image"):
        boot_disk.image = boot_disk_args.get("image")
      slurm.loginNodes.bootDisk = boot_disk
  if args.IsSpecified("slurm_prolog_scripts"):
    slurm.prologBashScripts = args.slurm_prolog_scripts
  if args.IsSpecified("slurm_epilog_scripts"):
    slurm.epilogBashScripts = args.slurm_epilog_scripts
  if args.IsKnownAndSpecified("slurm_task_prolog_scripts"):
    slurm.taskPrologBashScripts = args.slurm_task_prolog_scripts
  if args.IsKnownAndSpecified("slurm_task_epilog_scripts"):
    slurm.taskEpilogBashScripts = args.slurm_task_epilog_scripts
  if args.IsKnownAndSpecified("slurm_config"):
    slurm.config = messages_util.DictToMessageWithErrorCheck(
        args.slurm_config, message_module.SlurmConfig
    )
  if args.IsKnownAndSpecified("slurm_disable_health_check_program"):
    slurm.disableHealthCheckProgram = args.slurm_disable_health_check_program
  return slurm


def _GetOrCreateContainerNodePool(message_module, existing_node_set):
  """Gets or creates the containerNodePool for a SlurmNodeSet."""
  if not existing_node_set.containerNodePool:
    existing_node_set.containerNodePool = (
        message_module.ContainerNodePoolSlurmNodeSet()
    )
  return existing_node_set.containerNodePool


def _PatchBootDiskForNodeSet(
    message_module, *, existing_node_set, node_set_patch
):
  """Patches the bootDisk of a SlurmNodeSet."""
  if not existing_node_set.computeInstance:
    return
  if not existing_node_set.computeInstance.bootDisk:
    return
  boot_disk_patch = node_set_patch.get("bootDisk")

  # Determine the base bootDisk to patch.
  boot_disk = existing_node_set.computeInstance.bootDisk

  boot_disk.type = boot_disk_patch.get("type", boot_disk.type)
  boot_disk.sizeGb = boot_disk_patch.get("sizeGb", boot_disk.sizeGb)
  if hasattr(boot_disk, "image"):
    boot_disk.image = boot_disk_patch.get("image", boot_disk.image)

  # Assign the patched bootDisk to computeInstance.
  if not existing_node_set.computeInstance:
    existing_node_set.computeInstance = (
        message_module.ComputeInstanceSlurmNodeSet(bootDisk=boot_disk)
    )
  else:
    existing_node_set.computeInstance.bootDisk = boot_disk


def MakeClusterSlurmOrchestratorPatch(
    args, message_module, existing_cluster, cluster_patch, update_mask
):
  """Makes a cluster slurm orchestrator patch message with slurm fields."""
  slurm = message_module.SlurmOrchestrator()
  if args.IsSpecified("slurm_default_partition"):
    slurm.defaultPartition = args.slurm_default_partition
    update_mask.add("orchestrator.slurm.default_partition")

  existing_slurm_node_sets = None
  if (
      existing_cluster
      and existing_cluster.orchestrator
      and existing_cluster.orchestrator.slurm
  ):
    existing_slurm_node_sets = existing_cluster.orchestrator.slurm.nodeSets
  slurm_node_sets = _ConvertSlurmMessageToDict(existing_slurm_node_sets)
  is_node_sets_updated = False
  if args.IsSpecified("remove_slurm_node_sets"):
    for node_set_id in args.remove_slurm_node_sets:
      _RemoveKeyFromDictSpec(
          node_set_id, slurm_node_sets, _SLURM_NODESET_NOT_FOUND_ERROR
      )
      is_node_sets_updated = True
  if args.IsSpecified("update_slurm_node_sets"):
    for node_set in args.update_slurm_node_sets:
      node_set_id = node_set.get("id")
      existing_node_set = _GetValueFromDictSpec(
          node_set_id, slurm_node_sets, _SLURM_NODESET_NOT_FOUND_ERROR
      )
      node_set_keys = set(node_set.keys())
      is_gke_node_set = (
          getattr(existing_node_set, "containerNodePool", None) is not None
      )
      if is_gke_node_set and node_set_keys.intersection(_GCE_INSTANCE_FIELDS):
        raise ClusterDirectorError(_UPDATE_GCE_FIELDS_ON_GKE_NODE_SET_ERROR)
      elif not is_gke_node_set and node_set_keys.intersection(
          _GKE_NODE_POOL_FIELDS
      ):
        raise ClusterDirectorError(_UPDATE_GKE_FIELDS_ON_GCE_NODE_SET_ERROR)
      if "staticNodeCount" in node_set:
        existing_node_set.staticNodeCount = node_set.get("staticNodeCount")
      if "maxDynamicNodeCount" in node_set:
        existing_node_set.maxDynamicNodeCount = node_set.get(
            "maxDynamicNodeCount"
        )
      if "startupScriptTimeout" in node_set:
        if not existing_node_set.computeInstance:
          existing_node_set.computeInstance = (
              message_module.ComputeInstanceSlurmNodeSet()
          )
        existing_node_set.computeInstance.startupScriptTimeout = node_set.get(
            "startupScriptTimeout"
        )
      if "bootDisk" in node_set:
        _PatchBootDiskForNodeSet(
            message_module,
            existing_node_set=existing_node_set,
            node_set_patch=node_set)
      if "container-resource-labels" in node_set:
        _GetOrCreateContainerNodePool(message_module, existing_node_set)
        existing_node_set.containerNodePool.resourceLabels = MakeLabels(
            label_args=node_set.get("container-resource-labels"),
            label_cls=(
                message_module.ContainerNodePoolSlurmNodeSet
                .ResourceLabelsValue
            ),
        )
      if "container-startup-script" in node_set:
        _GetOrCreateContainerNodePool(message_module, existing_node_set)
        existing_node_set.containerNodePool.startupScript = _GetBashScript(
            node_set.get("container-startup-script")
        )

      slurm_node_sets[node_set_id] = existing_node_set
      is_node_sets_updated = True
  if args.IsSpecified("add_slurm_node_sets"):
    for node_set in args.add_slurm_node_sets:
      storage_configs_source = existing_cluster
      if (
          cluster_patch.storageResources
          and cluster_patch.storageResources.additionalProperties
      ):
        storage_configs_source = cluster_patch
      storage_configs = _GetStorageConfigs(
          message_module, storage_configs_source
      )
      node_set_keys = set(node_set.keys())
      node_set_type_str = node_set.get("type")
      has_gke_fields = node_set_keys.intersection(_GKE_NODE_POOL_FIELDS)
      is_gke_node_set = (
          node_set_type_str == NodeSetType.GKE.value
          or (node_set_type_str is None and has_gke_fields)
      )
      if not is_gke_node_set:
        compute_id = node_set.get("computeId")
        _GetComputeMachineTypeFromCluster(
            compute_id,
            cluster_patch,
            existing_cluster=existing_cluster,
            use_existing_cluster=True,
        )
      _AddKeyToDictSpec(
          key=node_set.get("id"),
          dict_spec=slurm_node_sets,
          value=_MakeSlurmNodeSet(
              message_module, node_set, storage_configs
          ),
          exception_message=_SLURM_NODESET_ALREADY_EXISTS_ERROR,
      )
      is_node_sets_updated = True
  if is_node_sets_updated:
    slurm.nodeSets = list(slurm_node_sets.values())
    if not slurm.nodeSets:
      raise ClusterDirectorError("Slurm nodesets cannot be empty.")
    update_mask.add("orchestrator.slurm.node_sets")

  existing_slurm_partitions = None
  if (
      existing_cluster
      and existing_cluster.orchestrator
      and existing_cluster.orchestrator.slurm
  ):
    existing_slurm_partitions = existing_cluster.orchestrator.slurm.partitions
  slurm_partitions = _ConvertSlurmMessageToDict(existing_slurm_partitions)
  is_partitions_updated = False
  if args.IsSpecified("remove_slurm_partitions"):
    for partition_id in args.remove_slurm_partitions:
      _RemoveKeyFromDictSpec(
          partition_id, slurm_partitions, _SLURM_PARTITION_NOT_FOUND_ERROR
      )
      is_partitions_updated = True
  if args.IsSpecified("update_slurm_partitions"):
    for partition in args.update_slurm_partitions:
      partition_id = partition.get("id")
      existing_partition = _GetValueFromDictSpec(
          partition_id, slurm_partitions, _SLURM_PARTITION_NOT_FOUND_ERROR
      )
      if "nodeSetIds" in partition:
        existing_partition.nodeSetIds = partition.get("nodeSetIds")
      if "exclusive" in partition:
        if hasattr(existing_partition, "exclusive"):
          existing_partition.exclusive = partition.get("exclusive")
      slurm_partitions[partition_id] = existing_partition
      is_partitions_updated = True
  if args.IsSpecified("add_slurm_partitions"):
    for partition in args.add_slurm_partitions:
      _AddKeyToDictSpec(
          key=partition.get("id"),
          dict_spec=slurm_partitions,
          value=_MakeSlurmPartition(message_module, partition),
          exception_message=_SLURM_PARTITION_ALREADY_EXISTS_ERROR,
      )
      is_partitions_updated = True
  if is_partitions_updated:
    slurm.partitions = list(slurm_partitions.values())
    if not slurm.partitions:
      raise ClusterDirectorError("Slurm partitions cannot be empty.")
    update_mask.add("orchestrator.slurm.partitions")

  if args.IsSpecified("update_slurm_login_node"):
    if (
        not existing_cluster
        or not existing_cluster.orchestrator
        or not existing_cluster.orchestrator.slurm
        or not existing_cluster.orchestrator.slurm.loginNodes
    ):
      raise ClusterDirectorError(
          "Login node is not part of existing cluster spec and cannot be "
          "updated."
      )
    login_nodes = existing_cluster.orchestrator.slurm.loginNodes
    login_node_patch = args.update_slurm_login_node

    if (count := login_node_patch.get("count")) is not None:
      login_nodes.count = count
    if (startup_script := login_node_patch.get("startupScript")) is not None:
      login_nodes.startupScript = _GetBashScript(startup_script)
    if (boot_disk_patch := login_node_patch.get("bootDisk")) is not None:
      boot_disk = login_nodes.bootDisk
      if boot_disk is None:
        boot_disk = message_module.BootDisk()
      boot_disk.type = boot_disk_patch.get("type", boot_disk.type)
      boot_disk.sizeGb = boot_disk_patch.get("sizeGb", boot_disk.sizeGb)
      if hasattr(boot_disk, "image"):
        boot_disk.image = boot_disk_patch.get("image", boot_disk.image)
      login_nodes.bootDisk = boot_disk
    slurm.loginNodes = login_nodes
    update_mask.add("orchestrator.slurm.login_nodes")

  if "storage_resources" in update_mask:
    new_storage_configs = _GetStorageConfigs(message_module, cluster_patch)
    if not slurm.nodeSets and slurm_node_sets:
      slurm.nodeSets = list(slurm_node_sets.values())
    if slurm.nodeSets:
      for ns in slurm.nodeSets:
        if not ns.storageConfigs:
          ns.storageConfigs = new_storage_configs
      update_mask.add("orchestrator.slurm.node_sets")

    if (
        not slurm.loginNodes
        and existing_cluster
        and existing_cluster.orchestrator
        and existing_cluster.orchestrator.slurm
        and existing_cluster.orchestrator.slurm.loginNodes
    ):
      slurm.loginNodes = existing_cluster.orchestrator.slurm.loginNodes
    if slurm.loginNodes and not slurm.loginNodes.storageConfigs:
      slurm.loginNodes.storageConfigs = new_storage_configs
      update_mask.add("orchestrator.slurm.login_nodes")

  return slurm
