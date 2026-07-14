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
from googlecloudsdk.command_lib.cluster_director.clusters import _validator
from googlecloudsdk.command_lib.cluster_director.clusters import errors
from googlecloudsdk.core.util import files

ClusterDirectorError = errors.ClusterDirectorError


def _GetStoragePoolZone(storage_pool: str) -> str:
  """Returns the storage pool zone from a storage pool resource string.

  Args:
    storage_pool: The storage pool resource string.

  Returns:
    The zone extracted from the storage pool string.

  Raises:
    ClusterDirectorError: If the storage pool string does not contain a zone.
  """

  # projects/{project}/zones/{zone}/storagePools/{storagePool}
  parts = storage_pool.split("/")
  for current_part, next_part in zip(parts, parts[1:]):
    if current_part == "zones" and next_part:
      return next_part
  raise ClusterDirectorError(
      f"Storage pool {storage_pool} does not contain a zone."
  )


def _GetStoragePoolName(cluster_ref: Any, storage_pool: str) -> str:
  """Returns the full storage pool name including project.

  Args:
    cluster_ref: The cluster resource reference.
    storage_pool: The storage pool string, which may or may not include
      'projects/'.

  Returns:
    The full storage pool name.

  Raises:
    ClusterDirectorError: If the storage pool string does not contain a zone.
  """
  if not cluster_ref:
    raise ClusterDirectorError(
        "Cluster reference is required to resolve storage pool name."
    )
  project = cluster_ref.Parent().projectsId
  if storage_pool.startswith("projects/"):
    storage_pool_name = storage_pool
  else:
    storage_pool_name = f"projects/{project}/{storage_pool}"
  _GetStoragePoolZone(storage_pool)
  return storage_pool_name


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


def _GetStorageConfigs(message_module, cluster, existing_storage_configs=None):
  """Returns the storage configs."""
  storage_configs: list[Any] = []
  if not cluster.storageResources:
    return storage_configs
  sorted_storages = sorted(
      cluster.storageResources.additionalProperties,
      key=lambda storage: storage.key,
  )
  if not sorted_storages:
    return storage_configs

  occupied_mounts = set()
  existing_mounts_by_id = {}
  counters = collections.defaultdict(int)
  if existing_storage_configs:
    for existing_sc in existing_storage_configs:
      occupied_mounts.add(existing_sc.localMount)
      existing_mounts_by_id[existing_sc.id] = existing_sc.localMount
      if existing_sc.localMount.startswith("/shared"):
        try:
          val = int(existing_sc.localMount[len("/shared"):])
          counters["filestore"] = max(counters["filestore"], val + 1)
        except ValueError:
          pass
      elif existing_sc.localMount.startswith("/scratch"):
        try:
          val = int(existing_sc.localMount[len("/scratch"):])
          counters["lustre"] = max(counters["lustre"], val + 1)
        except ValueError:
          pass
      elif existing_sc.localMount.startswith("/data"):
        try:
          val = int(existing_sc.localMount[len("/data"):])
          counters["bucket"] = max(counters["bucket"], val + 1)
        except ValueError:
          pass

  new_storages = [
      s for s in sorted_storages if s.key not in existing_mounts_by_id
  ]
  home_mounted_id = None
  if "/home" not in occupied_mounts and new_storages:
    home_mounted_id = new_storages[0].key

  for storage in sorted_storages:
    if storage.key in existing_mounts_by_id:
      storage_configs.append(
          message_module.StorageConfig(
              id=storage.key,
              localMount=existing_mounts_by_id[storage.key],
          )
      )
      continue

    if storage.key == home_mounted_id:
      storage_configs.append(
          message_module.StorageConfig(
              id=storage.key,
              localMount="/home",
          )
      )
      continue

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


def _MakeSlurmNodeSet(
    message_module, node_set, storage_configs, cluster_ref=None
):
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

  node_set_storage_configs = storage_configs
  if "storageConfigs" in node_set:
    node_set_storage_configs = [
        message_module.StorageConfig(
            id=sc.get("id"), localMount=sc.get("localMount")
        )
        for sc in node_set.get("storageConfigs")
    ]

  slurm_node_set = message_module.SlurmNodeSet(
      id=node_set.get("id"),
      staticNodeCount=node_set.get("staticNodeCount"),
      maxDynamicNodeCount=node_set.get("maxDynamicNodeCount"),
      storageConfigs=node_set_storage_configs,
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
      if compute_instance_boot_disk and hasattr(
          compute_instance_boot_disk, "storagePools"
      ):
        storage_pools = boot_disk.get("storagePools")
        if storage_pools is not None:
          compute_instance_boot_disk.storagePools = [
              _GetStoragePoolName(cluster_ref, p) for p in storage_pools
          ]
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


def MakeClusterSlurmOrchestrator(
    args, message_module, cluster, cluster_ref=None
):
  """Makes a cluster message with slurm orchestrator fields."""
  slurm = message_module.SlurmOrchestrator()
  default_storage_configs = _GetStorageConfigs(message_module, cluster)
  if args.IsSpecified("slurm_node_sets"):
    for node_set in args.slurm_node_sets:
      node_set_id = node_set.get("id")
      _validator.ValidateResourceID(node_set_id)
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
          _MakeSlurmNodeSet(
              message_module, node_set, storage_configs, cluster_ref
          )
      )

  if args.IsSpecified("slurm_partitions"):
    for partition in args.slurm_partitions:
      partition_id = partition.get("id")
      _validator.ValidateResourceID(partition_id)
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
      if hasattr(boot_disk, "storagePools"):
        storage_pools = boot_disk_args.get("storagePools")
        if storage_pools is not None:
          boot_disk.storagePools = [
              _GetStoragePoolName(cluster_ref, p) for p in storage_pools
          ]
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
    message_module, *, existing_node_set, node_set_patch, cluster_ref=None
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
  if hasattr(boot_disk, "storagePools"):
    storage_pools = boot_disk_patch.get("storagePools")
    if storage_pools is not None:
      boot_disk.storagePools = [
          _GetStoragePoolName(cluster_ref, p) for p in storage_pools
      ]

  # Assign the patched bootDisk to computeInstance.
  if not existing_node_set.computeInstance:
    existing_node_set.computeInstance = (
        message_module.ComputeInstanceSlurmNodeSet(bootDisk=boot_disk)
    )
  else:
    existing_node_set.computeInstance.bootDisk = boot_disk


def MakeClusterSlurmOrchestratorPatch(
    args,
    message_module,
    existing_cluster,
    cluster_patch,
    update_mask,
    cluster_ref=None,
):
  """Makes a cluster slurm orchestrator patch message with slurm fields."""
  slurm = message_module.SlurmOrchestrator()
  if args.IsSpecified("slurm_default_partition"):
    slurm.defaultPartition = args.slurm_default_partition
    update_mask.add("orchestrator.slurm.default_partition")

  storage_resources_map = {}
  if existing_cluster and existing_cluster.storageResources:
    for prop in existing_cluster.storageResources.additionalProperties:
      storage_resources_map[prop.key] = prop.value
  if cluster_patch and cluster_patch.storageResources:
    for prop in cluster_patch.storageResources.additionalProperties:
      storage_resources_map[prop.key] = prop.value

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
            node_set_patch=node_set,
            cluster_ref=cluster_ref,
        )
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

      if "storageConfigs" in node_set:
        existing_mounts_by_id = {}
        if existing_node_set.storageConfigs:
          existing_mounts_by_id = {
              esc.id: esc.localMount
              for esc in existing_node_set.storageConfigs
          }
        _validator.ValidateStorageConfigs(
            storage_resources_map,
            node_set.get("storageConfigs"),
            existing_mounts_by_id,
        )
        custom_storage_configs = [
            message_module.StorageConfig(
                id=sc.get("id"), localMount=sc.get("localMount")
            )
            for sc in node_set.get("storageConfigs")
        ]
        for ns in slurm_node_sets.values():
          ns.storageConfigs = custom_storage_configs

        if (
            not slurm.loginNodes
            and existing_cluster
            and existing_cluster.orchestrator
            and existing_cluster.orchestrator.slurm
            and existing_cluster.orchestrator.slurm.loginNodes
        ):
          slurm.loginNodes = existing_cluster.orchestrator.slurm.loginNodes
        if slurm.loginNodes:
          slurm.loginNodes.storageConfigs = custom_storage_configs
          update_mask.add("orchestrator.slurm.login_nodes")

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
      node_set_id = node_set.get("id")
      _validator.ValidateResourceID(node_set_id)
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
          key=node_set_id,
          dict_spec=slurm_node_sets,
          value=_MakeSlurmNodeSet(
              message_module, node_set, storage_configs, cluster_ref
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
      partition_id = partition.get("id")
      _validator.ValidateResourceID(partition_id)
      _AddKeyToDictSpec(
          key=partition_id,
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
      if hasattr(boot_disk, "storagePools"):
        storage_pools = boot_disk_patch.get("storagePools")
        if storage_pools is not None:
          boot_disk.storagePools = [
              _GetStoragePoolName(cluster_ref, p) for p in storage_pools
          ]
      login_nodes.bootDisk = boot_disk
    slurm.loginNodes = login_nodes
    update_mask.add("orchestrator.slurm.login_nodes")

  if "storage_resources" in update_mask:
    existing_storage_configs = []
    if (
        existing_cluster
        and existing_cluster.orchestrator
        and existing_cluster.orchestrator.slurm
        and existing_cluster.orchestrator.slurm.nodeSets
    ):
      existing_storage_configs = existing_cluster.orchestrator.slurm.nodeSets[
          0
      ].storageConfigs

    new_storage_configs = _GetStorageConfigs(
        message_module, cluster_patch, existing_storage_configs
    )

    if not slurm.nodeSets and slurm_node_sets:
      slurm.nodeSets = list(slurm_node_sets.values())

    removed_storage_ids = set()
    if (
        existing_cluster
        and existing_cluster.storageResources
        and cluster_patch
        and cluster_patch.storageResources
    ):
      existing_ids = {
          prop.key
          for prop in existing_cluster.storageResources.additionalProperties
      }
      updated_ids = {
          prop.key
          for prop in cluster_patch.storageResources.additionalProperties
      }
      removed_storage_ids = existing_ids - updated_ids

    if slurm.nodeSets:
      for ns in slurm.nodeSets:
        if ns.storageConfigs:
          ns.storageConfigs = [
              sc for sc in ns.storageConfigs if sc.id not in removed_storage_ids
          ]
        if not ns.storageConfigs:
          ns.storageConfigs = new_storage_configs
        else:
          existing_ids = {sc.id for sc in ns.storageConfigs}
          for sc in new_storage_configs:
            if sc.id not in existing_ids:
              ns.storageConfigs.append(sc)
      update_mask.add("orchestrator.slurm.node_sets")

    if (
        not slurm.loginNodes
        and existing_cluster
        and existing_cluster.orchestrator
        and existing_cluster.orchestrator.slurm
        and existing_cluster.orchestrator.slurm.loginNodes
    ):
      slurm.loginNodes = existing_cluster.orchestrator.slurm.loginNodes
    if slurm.loginNodes:
      node_sets = None
      if slurm.nodeSets:
        node_sets = slurm.nodeSets
      elif (
          existing_cluster
          and existing_cluster.orchestrator
          and existing_cluster.orchestrator.slurm
      ):
        node_sets = existing_cluster.orchestrator.slurm.nodeSets
      if node_sets:
        slurm.loginNodes.storageConfigs = node_sets[0].storageConfigs
        # Verify that the storageConfig update is successfully applied to the
        # login nodes
        if slurm.loginNodes.storageConfigs != node_sets[0].storageConfigs:
          raise ClusterDirectorError(
              "Login node storage configurations must match node set"
              " configurations."
          )
        update_mask.add("orchestrator.slurm.login_nodes")

  # Prolog scripts
  prolog_scripts = []
  if (
      existing_cluster
      and existing_cluster.orchestrator
      and existing_cluster.orchestrator.slurm
  ):
    prolog_scripts = existing_cluster.orchestrator.slurm.prologBashScripts or []

  is_prolog_updated = False
  if args.IsSpecified("remove_slurm_prolog_scripts"):
    prolog_scripts = [
        s for s in prolog_scripts if s not in args.remove_slurm_prolog_scripts
    ]
    is_prolog_updated = True
  if args.IsSpecified("add_slurm_prolog_scripts"):
    prolog_scripts.extend(args.add_slurm_prolog_scripts)
    is_prolog_updated = True

  if is_prolog_updated:
    slurm.prologBashScripts = prolog_scripts
    update_mask.add("orchestrator.slurm.prolog_bash_scripts")

  # Epilog scripts
  epilog_scripts = []
  if (
      existing_cluster
      and existing_cluster.orchestrator
      and existing_cluster.orchestrator.slurm
  ):
    epilog_scripts = existing_cluster.orchestrator.slurm.epilogBashScripts or []

  is_epilog_updated = False
  if args.IsSpecified("remove_slurm_epilog_scripts"):
    epilog_scripts = [
        s for s in epilog_scripts if s not in args.remove_slurm_epilog_scripts
    ]
    is_epilog_updated = True
  if args.IsSpecified("add_slurm_epilog_scripts"):
    epilog_scripts.extend(args.add_slurm_epilog_scripts)
    is_epilog_updated = True

  if is_epilog_updated:
    slurm.epilogBashScripts = epilog_scripts
    update_mask.add("orchestrator.slurm.epilog_bash_scripts")

  # Task Prolog scripts (v1alpha only or safe check)
  if args.IsKnownAndSpecified(
      "remove_slurm_task_prolog_scripts"
  ) or args.IsKnownAndSpecified("add_slurm_task_prolog_scripts"):
    task_prolog_scripts = []
    if (
        existing_cluster
        and existing_cluster.orchestrator
        and existing_cluster.orchestrator.slurm
    ):
      task_prolog_scripts = (
          existing_cluster.orchestrator.slurm.taskPrologBashScripts or []
      )

    is_task_prolog_updated = False
    if args.IsKnownAndSpecified("remove_slurm_task_prolog_scripts"):
      task_prolog_scripts = [
          s
          for s in task_prolog_scripts
          if s not in args.remove_slurm_task_prolog_scripts
      ]
      is_task_prolog_updated = True
    if args.IsKnownAndSpecified("add_slurm_task_prolog_scripts"):
      task_prolog_scripts.extend(args.add_slurm_task_prolog_scripts)
      is_task_prolog_updated = True

    if is_task_prolog_updated:
      slurm.taskPrologBashScripts = task_prolog_scripts
      update_mask.add("orchestrator.slurm.task_prolog_bash_scripts")

  # Task Epilog scripts (v1alpha only or safe check)
  if args.IsKnownAndSpecified(
      "remove_slurm_task_epilog_scripts"
  ) or args.IsKnownAndSpecified("add_slurm_task_epilog_scripts"):
    task_epilog_scripts = []
    if (
        existing_cluster
        and existing_cluster.orchestrator
        and existing_cluster.orchestrator.slurm
    ):
      task_epilog_scripts = (
          existing_cluster.orchestrator.slurm.taskEpilogBashScripts or []
      )

    is_task_epilog_updated = False
    if args.IsKnownAndSpecified("remove_slurm_task_epilog_scripts"):
      task_epilog_scripts = [
          s
          for s in task_epilog_scripts
          if s not in args.remove_slurm_task_epilog_scripts
      ]
      is_task_epilog_updated = True
    if args.IsKnownAndSpecified("add_slurm_task_epilog_scripts"):
      task_epilog_scripts.extend(args.add_slurm_task_epilog_scripts)
      is_task_epilog_updated = True

    if is_task_epilog_updated:
      slurm.taskEpilogBashScripts = task_epilog_scripts
      update_mask.add("orchestrator.slurm.task_epilog_bash_scripts")

  # Validate that all slurm node sets have identical storage configurations
  final_node_sets = None
  if slurm.nodeSets:
    final_node_sets = slurm.nodeSets
  elif (
      existing_cluster
      and existing_cluster.orchestrator
      and existing_cluster.orchestrator.slurm
  ):
    final_node_sets = existing_cluster.orchestrator.slurm.nodeSets

  if final_node_sets and len(final_node_sets) > 1:
    first_ns = final_node_sets[0]
    first_configs = first_ns.storageConfigs or []
    first_configs_map = {sc.id: sc.localMount for sc in first_configs}
    for ns in final_node_sets[1:]:
      current_configs = ns.storageConfigs or []
      current_configs_map = {sc.id: sc.localMount for sc in current_configs}
      if len(first_configs_map) != len(current_configs_map):
        raise ClusterDirectorError(
            "All Slurm node sets must have identical storage configurations. "
            f"Node set '{ns.id}' has a different number of storage configs "
            f"than '{first_ns.id}'."
        )
      for sc_id, local_mount in first_configs_map.items():
        if (
            sc_id not in current_configs_map
            or current_configs_map[sc_id] != local_mount
        ):
          raise ClusterDirectorError(
              "All Slurm node sets must have identical storage configurations. "
              f"Node set '{ns.id}' does not match '{first_ns.id}'."
          )

  return slurm
