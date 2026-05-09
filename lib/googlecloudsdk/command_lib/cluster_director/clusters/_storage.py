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

"""Storage configuration utilities for clusters command group."""

from __future__ import annotations

from typing import Any, Dict, Set

from googlecloudsdk.command_lib.cluster_director.clusters import errors

ClusterDirectorError = errors.ClusterDirectorError


def _GetFilestoreName(cluster_ref: Any, filestore: str) -> str:
  """Returns the filestore name."""
  project = cluster_ref.Parent().projectsId
  return f"projects/{project}/{filestore}"


def _GetLustreName(cluster_ref: Any, lustre: str) -> str:
  """Returns the Lustre name."""
  project = cluster_ref.Parent().projectsId
  return f"projects/{project}/{lustre}"


def _SetGcsAutoclassConfig(
    message_module: Any, gcs_message: Any, gcs_bucket_args: Dict[str, Any]
):
  """Sets the autoclass configuration on a NewBucketConfig message."""
  if gcs_bucket_args.get("enableAutoclass") or gcs_bucket_args.get(
      "terminalStorageClass"
  ):
    gcs_message.autoclass = message_module.GcsAutoclassConfig(enabled=True)
    if gcs_bucket_args.get("terminalStorageClass"):
      gcs_message.autoclass.terminalStorageClass = gcs_bucket_args.get(
          "terminalStorageClass"
      )


def _ConvertMessageToDict(message: Any) -> Dict[str, Any]:
  """Converts a message with AdditionalProperties to a dict.

  The input message is expected to contain a list of type
  AdditionalProperty(key=str, value=Any).

  Args:
    message: The message to convert.

  Returns:
    A dictionary representation of the message.
  """
  if not message:
    return {}
  return {each.key: each.value for each in message.additionalProperties}


def MakeClusterStorages(
    args: Any, message_module: Any, cluster_ref: Any
) -> Any:
  """Makes a cluster message with storage fields.

  Args:
    args: The argparse namespace.
    message_module: The API message module.
    cluster_ref: The cluster resource reference.

  Returns:
    A message_module.Cluster.StorageResourcesValue object.

  Raises:
    ClusterDirectorError: If duplicate storage ids are provided.
  """
  storages = message_module.Cluster.StorageResourcesValue()
  storage_ids = set()
  if args.IsSpecified("create_filestores"):
    for filestore in args.create_filestores:
      storage_id = filestore.get("id")
      if storage_id in storage_ids:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      storage_ids.add(storage_id)
      storages.additionalProperties.append(
          message_module.Cluster.StorageResourcesValue.AdditionalProperty(
              key=filestore.get("id"),
              value=message_module.StorageResource(
                  config=message_module.StorageResourceConfig(
                      newFilestore=message_module.NewFilestoreConfig(
                          filestore=_GetFilestoreName(
                              cluster_ref, filestore.get("name")
                          ),
                          tier=filestore.get("tier"),
                          fileShares=[
                              message_module.FileShareConfig(
                                  capacityGb=filestore.get("capacityGb"),
                                  fileShare=filestore.get("fileshare"),
                              )
                          ],
                          protocol=filestore.get("protocol"),
                          description=filestore.get("description"),
                      )
                  ),
              ),
          )
      )
  if args.IsSpecified("filestores"):
    for filestore in args.filestores:
      storage_id = filestore.get("id")
      if storage_id in storage_ids:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      storage_ids.add(storage_id)
      storages.additionalProperties.append(
          message_module.Cluster.StorageResourcesValue.AdditionalProperty(
              key=storage_id,
              value=message_module.StorageResource(
                  config=message_module.StorageResourceConfig(
                      existingFilestore=message_module.ExistingFilestoreConfig(
                          filestore=_GetFilestoreName(
                              cluster_ref, filestore.get("name")
                          ),
                      )
                  ),
              ),
          )
      )
  if args.IsSpecified("create_lustres"):
    for lustre in args.create_lustres:
      storage_id = lustre.get("id")
      if storage_id in storage_ids:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      storage_ids.add(storage_id)
      storages.additionalProperties.append(
          message_module.Cluster.StorageResourcesValue.AdditionalProperty(
              key=storage_id,
              value=message_module.StorageResource(
                  config=message_module.StorageResourceConfig(
                      newLustre=message_module.NewLustreConfig(
                          lustre=_GetLustreName(
                              cluster_ref, lustre.get("name")
                          ),
                          filesystem=lustre.get("filesystem"),
                          capacityGb=lustre.get("capacityGb"),
                          description=lustre.get("description"),
                          perUnitStorageThroughput=lustre.get(
                              "perUnitStorageThroughput"
                          ),
                      )
                  ),
              ),
          )
      )
  if args.IsSpecified("lustres"):
    for lustre in args.lustres:
      storage_id = lustre.get("id")
      if storage_id in storage_ids:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      storage_ids.add(storage_id)
      storages.additionalProperties.append(
          message_module.Cluster.StorageResourcesValue.AdditionalProperty(
              key=storage_id,
              value=message_module.StorageResource(
                  config=message_module.StorageResourceConfig(
                      existingLustre=message_module.ExistingLustreConfig(
                          lustre=_GetLustreName(
                              cluster_ref, lustre.get("name")
                          ),
                      )
                  ),
              ),
          )
      )
  if args.IsSpecified("create_buckets"):
    for gcs_bucket in args.create_buckets:
      storage_id = gcs_bucket.get("id")
      if storage_id in storage_ids:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      storage_ids.add(storage_id)
      gcs = message_module.NewBucketConfig(
          bucket=gcs_bucket.get("name"),
      )
      if "storageClass" in gcs_bucket:
        gcs.storageClass = gcs_bucket.get("storageClass")
      else:
        _SetGcsAutoclassConfig(message_module, gcs, gcs_bucket)
      # If neither storageClass nor autoclass is set, set storageClass to
      # STANDARD by default.
      if not gcs.storageClass and not gcs.autoclass:
        gcs.storageClass = (
            message_module.NewBucketConfig.StorageClassValueValuesEnum.STANDARD
        )
      if "enableHNS" in gcs_bucket:
        gcs.hierarchicalNamespace = (
            message_module.GcsHierarchicalNamespaceConfig(
                enabled=gcs_bucket.get("enableHNS"),
            )
        )
      storages.additionalProperties.append(
          message_module.Cluster.StorageResourcesValue.AdditionalProperty(
              key=storage_id,
              value=message_module.StorageResource(
                  config=message_module.StorageResourceConfig(newBucket=gcs)
              ),
          ),
      )
  if args.IsSpecified("buckets"):
    for gcs_bucket in args.buckets:
      storage_id = gcs_bucket.get("id")
      if storage_id in storage_ids:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      storage_ids.add(storage_id)
      storages.additionalProperties.append(
          message_module.Cluster.StorageResourcesValue.AdditionalProperty(
              key=storage_id,
              value=message_module.StorageResource(
                  config=message_module.StorageResourceConfig(
                      existingBucket=message_module.ExistingBucketConfig(
                          bucket=gcs_bucket.get("name"),
                      )
                  ),
              ),
          )
      )
  return storages


def MakeClusterStoragesPatch(
    args: Any,
    message_module: Any,
    cluster_ref: Any,
    existing_cluster: Any,
    update_mask: Set[str],
) -> Any:
  """Makes a cluster patch message with storage fields.

  Args:
    args: The argparse namespace.
    message_module: The API message module.
    cluster_ref: The cluster resource reference.
    existing_cluster: The existing cluster message.
    update_mask: A set of field paths to update.

  Returns:
    A message_module.Cluster.StorageResourcesValue object with patched fields.

  Raises:
    ClusterDirectorError: If any storage resources specified for removal are
      not found, or if duplicate storage IDs are provided for addition.
  """
  storage_resources = message_module.Cluster.StorageResourcesValue()
  storages = _ConvertMessageToDict(
      existing_cluster.storageResources if existing_cluster else None
  )
  is_storage_updated = False

  if args.IsSpecified("remove_filestore_instances"):
    filestores_to_remove = {
        _GetFilestoreName(cluster_ref, f)
        for f in args.remove_filestore_instances
    }
    storage_ids_to_remove = set()
    found_filestores = set()

    for storage_id, storage_resource in storages.items():
      config = storage_resource.config
      filestore_name = None
      if config and config.newFilestore:
        filestore_name = config.newFilestore.filestore
      elif config and config.existingFilestore:
        filestore_name = config.existingFilestore.filestore

      if filestore_name in filestores_to_remove:
        storage_ids_to_remove.add(storage_id)
        found_filestores.add(filestore_name)

    if found_filestores != filestores_to_remove:
      not_found = filestores_to_remove - found_filestores
      raise ClusterDirectorError(
          f"Filestore(s) not found: {', '.join(not_found)}"
      )

    for storage_id in storage_ids_to_remove:
      storages.pop(storage_id)
    is_storage_updated = True

  if args.IsSpecified("remove_storage_buckets"):
    buckets_to_remove = set(args.remove_storage_buckets)
    storage_ids_to_remove = set()
    found_buckets = set()

    for storage_id, storage_resource in storages.items():
      config = storage_resource.config
      bucket_name = None
      if config:
        if config.newBucket:
          bucket_name = config.newBucket.bucket
        elif config.existingBucket:
          bucket_name = config.existingBucket.bucket

      if bucket_name in buckets_to_remove:
        storage_ids_to_remove.add(storage_id)
        found_buckets.add(bucket_name)

    if found_buckets != buckets_to_remove:
      not_found = buckets_to_remove - found_buckets
      raise ClusterDirectorError(
          "Cloud Storage bucket(s) not found:"
          f" {', '.join(sorted(list(not_found)))}"
      )

    for storage_id in storage_ids_to_remove:
      storages.pop(storage_id)
    is_storage_updated = True

  if args.IsSpecified("remove_lustre_instances"):
    lustres_to_remove = {
        _GetLustreName(cluster_ref, f) for f in args.remove_lustre_instances
    }
    storage_ids_to_remove = set()
    found_lustres = set()

    for storage_id, storage_resource in storages.items():
      config = storage_resource.config
      lustre_name = None
      if config and config.newLustre:
        lustre_name = config.newLustre.lustre
      elif config and config.existingLustre:
        lustre_name = config.existingLustre.lustre

      if lustre_name in lustres_to_remove:
        storage_ids_to_remove.add(storage_id)
        found_lustres.add(lustre_name)

    if found_lustres != lustres_to_remove:
      not_found = lustres_to_remove - found_lustres
      raise ClusterDirectorError(f"Lustre(s) not found: {', '.join(not_found)}")

    for storage_id in storage_ids_to_remove:
      storages.pop(storage_id)
    is_storage_updated = True

  if args.IsSpecified("add_new_filestore_instances"):
    for filestore in args.add_new_filestore_instances:
      storage_id = filestore.get("id")
      if storage_id in storages:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      filestore_name = _GetFilestoreName(cluster_ref, filestore.get("name"))
      for storage_resource in storages.values():
        config = storage_resource.config
        if config and (
            (
                config.newFilestore
                and config.newFilestore.filestore == filestore_name
            )
            or (
                config.existingFilestore
                and config.existingFilestore.filestore == filestore_name
            )
        ):
          raise ClusterDirectorError(
              f"Filestore {filestore_name} already exists."
          )

      storages[storage_id] = message_module.StorageResource(
          config=message_module.StorageResourceConfig(
              newFilestore=message_module.NewFilestoreConfig(
                  filestore=filestore_name,
                  tier=filestore.get("tier"),
                  fileShares=[
                      message_module.FileShareConfig(
                          capacityGb=filestore.get("capacityGb"),
                          fileShare=filestore.get("fileshare"),
                      )
                  ],
                  protocol=filestore.get("protocol"),
                  description=filestore.get("description"),
              )
          )
      )
    is_storage_updated = True

  if args.IsSpecified("add_filestore_instances"):
    for filestore in args.add_filestore_instances:
      storage_id = filestore.get("id")
      if storage_id in storages:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      filestore_name = _GetFilestoreName(cluster_ref, filestore.get("name"))
      for storage_resource in storages.values():
        config = storage_resource.config
        if config and (
            (
                config.newFilestore
                and config.newFilestore.filestore == filestore_name
            )
            or (
                config.existingFilestore
                and config.existingFilestore.filestore == filestore_name
            )
        ):
          raise ClusterDirectorError(
              f"Filestore {filestore_name} already exists."
          )

      storages[storage_id] = message_module.StorageResource(
          config=message_module.StorageResourceConfig(
              existingFilestore=message_module.ExistingFilestoreConfig(
                  filestore=filestore_name,
              )
          )
      )
    is_storage_updated = True

  if args.IsSpecified("add_new_lustre_instances"):
    for lustre in args.add_new_lustre_instances:
      storage_id = lustre.get("id")
      if storage_id in storages:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      lustre_name = _GetLustreName(cluster_ref, lustre.get("name"))
      for storage_resource in storages.values():
        config = storage_resource.config
        if config and (
            (config.newLustre and config.newLustre.lustre == lustre_name)
            or (
                config.existingLustre
                and config.existingLustre.lustre == lustre_name
            )
        ):
          raise ClusterDirectorError(f"Lustre {lustre_name} already exists.")

      storages[storage_id] = message_module.StorageResource(
          config=message_module.StorageResourceConfig(
              newLustre=message_module.NewLustreConfig(
                  lustre=_GetLustreName(cluster_ref, lustre.get("name")),
                  filesystem=lustre.get("filesystem"),
                  capacityGb=lustre.get("capacityGb"),
                  description=lustre.get("description"),
                  perUnitStorageThroughput=lustre.get(
                      "perUnitStorageThroughput"
                  ),
              )
          )
      )
    is_storage_updated = True

  if args.IsSpecified("add_lustre_instances"):
    for lustre in args.add_lustre_instances:
      storage_id = lustre.get("id")
      if storage_id in storages:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      lustre_name = _GetLustreName(cluster_ref, lustre.get("name"))
      for storage_resource in storages.values():
        config = storage_resource.config
        if config and (
            (config.newLustre and config.newLustre.lustre == lustre_name)
            or (
                config.existingLustre
                and config.existingLustre.lustre == lustre_name
            )
        ):
          raise ClusterDirectorError(f"Lustre {lustre_name} already exists.")

      storages[storage_id] = message_module.StorageResource(
          config=message_module.StorageResourceConfig(
              existingLustre=message_module.ExistingLustreConfig(
                  lustre=lustre_name,
              )
          )
      )
    is_storage_updated = True

  if args.IsSpecified("add_storage_buckets"):
    for bucket in args.add_storage_buckets:
      storage_id = bucket.get("id")
      if storage_id in storages:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      bucket_name = bucket.get("name")
      # Check for duplicates
      for storage_resource in storages.values():
        config = storage_resource.config
        bucket_name_in_config = None
        if config:
          if config.newBucket:
            bucket_name_in_config = config.newBucket.bucket
          elif config.existingBucket:
            bucket_name_in_config = config.existingBucket.bucket

        if bucket_name_in_config == bucket_name:
          raise ClusterDirectorError(
              f"Cloud Storage bucket {bucket_name} already exists."
          )

      storages[storage_id] = message_module.StorageResource(
          config=message_module.StorageResourceConfig(
              existingBucket=message_module.ExistingBucketConfig(
                  bucket=bucket_name,
              )
          )
      )
    is_storage_updated = True

  if args.IsSpecified("add_new_storage_buckets"):
    for gcs_bucket in args.add_new_storage_buckets:
      storage_id = gcs_bucket.get("id")
      if storage_id in storages:
        raise ClusterDirectorError(
            f"Duplicate storage resource id: {storage_id}"
        )
      bucket_name = gcs_bucket.get("name")
      for storage_resource in storages.values():
        config = storage_resource.config
        b_name = None
        if config:
          if config.newBucket:
            b_name = config.newBucket.bucket
          elif config.existingBucket:
            b_name = config.existingBucket.bucket
        if b_name == bucket_name:
          raise ClusterDirectorError(
              f"Cloud Storage bucket {bucket_name} already exists."
          )
      gcs = message_module.NewBucketConfig(
          bucket=gcs_bucket.get("name"),
      )
      if "storageClass" in gcs_bucket:
        gcs.storageClass = gcs_bucket.get("storageClass")
      else:
        _SetGcsAutoclassConfig(message_module, gcs, gcs_bucket)
      if not gcs.storageClass and not gcs.autoclass:
        gcs.storageClass = (
            message_module.NewBucketConfig.StorageClassValueValuesEnum.STANDARD
        )
      if "enableHNS" in gcs_bucket:
        gcs.hierarchicalNamespace = (
            message_module.GcsHierarchicalNamespaceConfig(
                enabled=gcs_bucket.get("enableHNS"),
            )
        )
      storages[storage_id] = message_module.StorageResource(
          config=message_module.StorageResourceConfig(newBucket=gcs)
      )
    is_storage_updated = True

  if is_storage_updated:
    storage_resources.additionalProperties = [
        message_module.Cluster.StorageResourcesValue.AdditionalProperty(
            key=key, value=value
        )
        for key, value in storages.items()
    ]
    update_mask.add("storage_resources")
  return storage_resources
