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

"""Flag type definitions for clusters command group."""

from typing import Any
from googlecloudsdk.api_lib.hypercomputecluster import utils as api_utils
from googlecloudsdk.calliope import arg_parsers


UPDATE_MASK_OBJECT = arg_parsers.ArgObject(
    value_type=str, enable_shorthand=True
)

NETWORK_OBJECT = arg_parsers.ArgObject(
    spec={
        "name": str,
        "description": str,
    },
    required_keys=["name"],
    enable_shorthand=True,
)

LABEL = arg_parsers.ArgObject(
    key_type=str,
    value_type=str,
    enable_shorthand=True,
)

STORAGE_CONFIG = arg_parsers.ArgObject(
    spec={
        "id": str,
        "localMount": str,
    },
    repeated=True,
)

LUSTRES_OBJECT = arg_parsers.ArgObject(
    spec={
        "name": str,
        "filesystem": str,
        "capacityGb": int,
        "description": str,
        "perUnitStorageThroughput": int,
    },
    required_keys=["name", "capacityGb", "filesystem"],
    enable_shorthand=True,
    repeated=True,
)

SERVICE_ACCOUNT_TYPE = arg_parsers.ArgObject(
    spec={
        "email": str,
        "scopes": arg_parsers.ArgList(),
    }
)

SLURM_CONFIG_TYPE = arg_parsers.ArgObject(
    spec={
        "requeueExitCodes": arg_parsers.ArgList(element_type=int),
        "requeueHoldExitCodes": arg_parsers.ArgList(element_type=int),
        "prologFlags": arg_parsers.ArgList(element_type=str),
        "prologEpilogTimeout": str,
        "accountingStorageEnforceFlags": arg_parsers.ArgList(element_type=str),
        "priorityType": str,
        "priorityWeightAge": int,
        "priorityWeightAssoc": int,
        "priorityWeightFairshare": int,
        "priorityWeightJobSize": int,
        "priorityWeightPartition": int,
        "priorityWeightQos": int,
        "priorityWeightTres": str,
        "preemptMode": arg_parsers.ArgList(element_type=str),
        "preemptType": str,
        "preemptExemptTime": str,
        "healthCheckInterval": int,
        "healthCheckNodeState": str,
        "healthCheckProgram": str,
    }
)
FILESTORE_CONFIG_SPEC = {
    "description": str,
    "fileShares": arg_parsers.ArgObject(
        spec={"capacityGb": int, "fileShare": str},
        repeated=True,
    ),
    "filestore": str,
    "protocol": str,
    "tier": str,
}

LUSTRE_CONFIG_SPEC = {
    "capacityGb": int,
    "description": str,
    "filesystem": str,
    "lustre": str,
}


class FlagTypes:
  """Generates flag types for clusters commands.

  Attributes:
    messages: The messages module for the given API version.
    is_alpha: True if the API version is v1alpha.
  """

  def __init__(self, api_version: str) -> None:
    """Initializes FlagTypes.

    Args:
      api_version: The API version string, e.g., 'v1alpha' or 'v1beta'.
    """

    self.messages = api_utils.GetMessagesModule(
        api_utils.GetReleaseTrack(api_version)
    )
    self.is_alpha = api_version == "v1alpha"

  def GetFilestoresObject(self) -> arg_parsers.ArgObject:
    return arg_parsers.ArgObject(
        spec={
            "name": str,
            "tier": self.messages.NewFilestoreConfig.TierValueValuesEnum,
            "capacityGb": int,
            "fileshare": str,
            "protocol": (
                self.messages.NewFilestoreConfig.ProtocolValueValuesEnum
            ),
            "description": str,
        },
        required_keys=["name", "tier", "capacityGb", "fileshare"],
        enable_shorthand=True,
        repeated=True,
    )

  def GetProtoBootDiskType(self) -> arg_parsers.ArgObject:
    spec = {
        "type": str,
        "sizeGb": int,
    }
    if self.is_alpha:
      spec["image"] = str
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["type", "sizeGb"],
        enable_shorthand=True,
    )

  def GetGcsBucketsObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing GCS bucket configurations."""

    spec = {
        "name": str,
        "storageClass": (
            self.messages.NewBucketConfig.StorageClassValueValuesEnum
        ),
        "enableAutoclass": bool,
        "enableHNS": bool,
    }
    if self.is_alpha:
      spec["terminalStorageClass"] = (
          self.messages.GcsAutoclassConfig.TerminalStorageClassValueValuesEnum
      )
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["name"],
        enable_shorthand=True,
        repeated=True,
    )

  def GetOnDemandInstancesObject(self) -> arg_parsers.ArgObject:
    spec = {
        "id": str,
        "zone": str,
        "machineType": str,
    }
    if self.is_alpha:
      spec["atmTags"] = LABEL
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["id", "zone", "machineType"],
        enable_shorthand=True,
        repeated=True,
    )

  def GetSpotInstancesObject(self) -> arg_parsers.ArgObject:
    spec = {
        "id": str,
        "zone": str,
        "machineType": str,
        "terminationAction": (
            self.messages.NewSpotInstancesConfig.TerminationActionValueValuesEnum
        ),
    }
    if self.is_alpha:
      spec["atmTags"] = LABEL
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["id", "zone", "machineType"],
        enable_shorthand=True,
        repeated=True,
    )

  def GetReservedInstancesObject(self) -> arg_parsers.ArgObject:
    spec = {
        "id": str,
        "reservation": str,
    }
    if self.is_alpha:
      spec.update({
          "atmTags": LABEL,
          "reservationBlock": str,
          "reservationSubBlock": str,
      })
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["id"],
        enable_shorthand=True,
        repeated=True,
    )

  def GetFlexStartInstancesObject(self) -> arg_parsers.ArgObject:
    spec = {
        "id": str,
        "zone": str,
        "machineType": str,
        "maxDuration": str,
    }
    if self.is_alpha:
      spec["atmTags"] = LABEL
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["id", "zone", "machineType", "maxDuration"],
        enable_shorthand=True,
        repeated=True,
    )

  def GetSlurmNodeSetsObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing Slurm Node Sets configurations."""
    if self.is_alpha:
      return arg_parsers.ArgObject(
          spec={
              "id": str,
              "computeId": str,
              "staticNodeCount": int,
              "maxDynamicNodeCount": int,
              "startupScript": arg_parsers.ArgObject(),
              "labels": LABEL,
              "bootDisk": self.GetProtoBootDiskType(),
              "startupScriptTimeout": str,
              "container-resource-labels": LABEL,
              "container-startup-script": arg_parsers.ArgObject(),
              "type": str,
              "storageConfigs": STORAGE_CONFIG,
          },
          required_keys=["id"],
          enable_shorthand=True,
          repeated=True,
      )
    else:
      return arg_parsers.ArgObject(
          spec={
              "id": str,
              "computeId": str,
              "staticNodeCount": int,
              "maxDynamicNodeCount": int,
              "computeInstance": arg_parsers.ArgObject(
                  spec={
                      "startupScript": str,
                      "labels": LABEL,
                      "bootDisk": self.GetProtoBootDiskType(),
                  },
                  enable_shorthand=True,
              ),
              "storageConfigs": STORAGE_CONFIG,
          },
          required_keys=["id"],
          enable_shorthand=True,
          repeated=True,
      )

  def _GetSlurmPartitionSpec(self) -> dict[str, Any]:
    spec = {
        "id": str,
        "nodeSetIds": arg_parsers.ArgObject(value_type=str, repeated=True),
    }
    if self.is_alpha:
      spec["exclusive"] = bool
    return spec

  def GetSlurmPartitionsObject(self) -> arg_parsers.ArgObject:
    return arg_parsers.ArgObject(
        spec=self._GetSlurmPartitionSpec(),
        required_keys=["id", "nodeSetIds"],
        enable_shorthand=True,
        repeated=True,
    )

  def GetSlurmPartitionsUpdateObject(self) -> arg_parsers.ArgObject:
    return arg_parsers.ArgObject(
        spec=self._GetSlurmPartitionSpec(),
        required_keys=["id"],
        enable_shorthand=True,
        repeated=True,
    )

  def GetSlurmLoginNodeObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing Slurm Login Node configurations."""
    if self.is_alpha:
      return arg_parsers.ArgObject(
          spec={
              "machineType": str,
              "zone": str,
              "count": int,
              "enableOsLogin": bool,
              "enablePublicIps": bool,
              "startupScript": arg_parsers.ArgObject(),
              "labels": LABEL,
              "bootDisk": self.GetProtoBootDiskType(),
              "storageConfigs": STORAGE_CONFIG,
          },
          required_keys=["machineType", "zone"],
          enable_shorthand=True,
      )
    else:
      return arg_parsers.ArgObject(
          spec={
              "machineType": str,
              "zone": str,
              "count": int,
              "enableOsLogin": bool,
              "enablePublicIps": bool,
              "startupScript": str,
              "labels": LABEL,
              "bootDisk": self.GetProtoBootDiskType(),
              "storageConfigs": STORAGE_CONFIG,
          },
          required_keys=["machineType", "zone"],
          enable_shorthand=True,
      )

  def GetSlurmLoginNodeUpdateObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing Slurm Login Node update configurations."""
    if self.is_alpha:
      return arg_parsers.ArgObject(
          spec={
              "count": int,
              "startupScript": arg_parsers.ArgObject(),
              "bootDisk": self.GetProtoBootDiskType(),
          },
          required_keys=[],
          enable_shorthand=True,
      )
    else:
      return arg_parsers.ArgObject(
          spec={
              "count": int,
              "startupScript": str,
              "bootDisk": self.GetProtoBootDiskType(),
          },
          required_keys=[],
          enable_shorthand=True,
      )

  def GetClusterFlagType(self) -> dict[str, Any]:
    """Returns cluster flag type for create command."""
    if self.is_alpha:
      new_on_demand_instances_spec = {
          "machineType": str,
          "zone": str,
          "atmTags": LABEL,
      }
      new_spot_instances_spec = new_on_demand_instances_spec | {
          "terminationAction": str
      }
      new_flex_start_instances_spec = new_spot_instances_spec | {
          "maxDuration": str
      }
      new_reserved_instances_spec = new_on_demand_instances_spec | {
          "reservation": str,
          "type": str,
          "reservationBlock": str,
          "reservationSubBlock": str,
      }
      bucket_config_spec = {
          "autoclass": arg_parsers.ArgObject(
              spec={
                  "enabled": bool,
                  "terminalStorageClass": str,
              }
          ),
          "bucket": str,
          "hierarchicalNamespace": arg_parsers.ArgObject(
              spec={"enabled": bool}
          ),
          "storageClass": str,
      }
      return {
          "computeResources": arg_parsers.ArgObject(
              key_type=str,
              value_type=arg_parsers.ArgObject(
                  spec={
                      "config": arg_parsers.ArgObject(
                          spec={
                              "newFlexStartInstances": arg_parsers.ArgObject(
                                  spec=new_flex_start_instances_spec
                              ),
                              "newDwsFlexInstances": arg_parsers.ArgObject(
                                  spec=new_flex_start_instances_spec
                              ),
                              "newOnDemandInstances": arg_parsers.ArgObject(
                                  spec=new_on_demand_instances_spec
                              ),
                              "newReservedInstances": arg_parsers.ArgObject(
                                  spec=new_reserved_instances_spec
                              ),
                              "newSpotInstances": arg_parsers.ArgObject(
                                  spec=new_spot_instances_spec
                              ),
                          }
                      ),
                  }
              ),
          ),
          "description": str,
          "labels": LABEL,
          "name": str,
          "networkResources": arg_parsers.ArgObject(
              key_type=str,
              value_type=arg_parsers.ArgObject(
                  spec={
                      "config": arg_parsers.ArgObject(
                          spec={
                              "existingNetwork": arg_parsers.ArgObject(
                                  spec={
                                      "network": str,
                                      "subnetwork": str,
                                  }
                              ),
                              "newNetwork": arg_parsers.ArgObject(
                                  spec={
                                      "description": str,
                                      "network": str,
                                  }
                              ),
                              "newComputeNetwork": arg_parsers.ArgObject(
                                  spec={
                                      "description": str,
                                      "network": str,
                                  }
                              ),
                              "existingComputeNetwork": arg_parsers.ArgObject(
                                  spec={
                                      "network": str,
                                      "subnetwork": str,
                                  }
                              ),
                          }
                      ),
                  }
              ),
          ),
          "orchestrator": arg_parsers.ArgObject(
              spec={
                  "slurm": arg_parsers.ArgObject(
                      spec={
                          "defaultPartition": str,
                          "loginNodes": arg_parsers.ArgObject(
                              spec={
                                  "count": int,
                                  "enableOsLogin": bool,
                                  "enablePublicIps": bool,
                                  "labels": LABEL,
                                  "machineType": str,
                                  "startupScript": arg_parsers.ArgObject(),
                                  "storageConfigs": STORAGE_CONFIG,
                                  "zone": str,
                                  "bootDisk": self.GetProtoBootDiskType(),
                              }
                          ),
                          "nodeSets": arg_parsers.ArgObject(
                              spec={
                                  "id": str,
                                  "maxDynamicNodeCount": int,
                                  "staticNodeCount": int,
                                  "storageConfigs": STORAGE_CONFIG,
                                  "computeId": str,
                                  "computeInstance": arg_parsers.ArgObject(
                                      spec={
                                          "startupScript": (
                                              arg_parsers.ArgObject()
                                          ),
                                          "labels": LABEL,
                                          "bootDisk": (
                                              self.GetProtoBootDiskType()
                                          ),
                                          "startupScriptTimeout": str,
                                      }
                                  ),
                                  "containerNodePool": arg_parsers.ArgObject(
                                      spec={}
                                  ),
                              },
                              repeated=True,
                          ),
                          "partitions": arg_parsers.ArgObject(
                              spec={
                                  "exclusive": bool,
                                  "id": str,
                                  "nodeSetIds": arg_parsers.ArgObject(
                                      repeated=True,
                                  ),
                              },
                              repeated=True,
                          ),
                          "prologBashScripts": arg_parsers.ArgList(),
                          "epilogBashScripts": arg_parsers.ArgList(),
                          "taskPrologBashScripts": arg_parsers.ArgList(),
                          "taskEpilogBashScripts": arg_parsers.ArgList(),
                          "config": SLURM_CONFIG_TYPE,
                          "disableHealthCheckProgram": bool,
                      }
                  ),
              }
          ),
          "storageResources": arg_parsers.ArgObject(
              key_type=str,
              value_type=arg_parsers.ArgObject(
                  spec={
                      "config": arg_parsers.ArgObject(
                          spec={
                              "existingBucket": arg_parsers.ArgObject(
                                  spec={"bucket": str}
                              ),
                              "existingFilestore": arg_parsers.ArgObject(
                                  spec={"filestore": str}
                              ),
                              "existingLustre": arg_parsers.ArgObject(
                                  spec={"lustre": str}
                              ),
                              "newBucket": arg_parsers.ArgObject(
                                  spec=bucket_config_spec
                              ),
                              "newFilestore": arg_parsers.ArgObject(
                                  spec=FILESTORE_CONFIG_SPEC
                              ),
                              "newLustre": arg_parsers.ArgObject(
                                  spec=LUSTRE_CONFIG_SPEC
                                  | {"perUnitStorageThroughput": int}
                              ),
                          },
                      )
                  }
              ),
          ),
      }
    else:  # Beta
      new_on_demand_instances_beta_spec = {
          "machineType": str,
          "zone": str,
      }
      new_spot_instances_beta_spec = new_on_demand_instances_beta_spec | {
          "terminationAction": str
      }
      new_flex_start_instances_beta_spec = new_on_demand_instances_beta_spec | {
          "maxDuration": str
      }
      new_reserved_instances_beta_spec = {
          "reservation": str,
      }
      bucket_config_beta_spec = {
          "autoclass": arg_parsers.ArgObject(
              spec={
                  "enabled": bool,
              }
          ),
          "bucket": str,
          "hierarchicalNamespace": arg_parsers.ArgObject(
              spec={"enabled": bool}
          ),
          "storageClass": str,
      }
      return {
          "computeResources": arg_parsers.ArgObject(
              key_type=str,
              value_type=arg_parsers.ArgObject(
                  spec={
                      "config": arg_parsers.ArgObject(
                          spec={
                              "newFlexStartInstances": arg_parsers.ArgObject(
                                  spec=new_flex_start_instances_beta_spec
                              ),
                              "newDwsFlexInstances": arg_parsers.ArgObject(
                                  spec=new_flex_start_instances_beta_spec
                              ),
                              "newOnDemandInstances": arg_parsers.ArgObject(
                                  spec=new_on_demand_instances_beta_spec
                              ),
                              "newReservedInstances": arg_parsers.ArgObject(
                                  spec=new_reserved_instances_beta_spec
                              ),
                              "newSpotInstances": arg_parsers.ArgObject(
                                  spec=new_spot_instances_beta_spec
                              ),
                          }
                      ),
                  }
              ),
          ),
          "description": str,
          "labels": LABEL,
          "name": str,
          "networkResources": arg_parsers.ArgObject(
              key_type=str,
              value_type=arg_parsers.ArgObject(
                  spec={
                      "config": arg_parsers.ArgObject(
                          spec={
                              "existingNetwork": arg_parsers.ArgObject(
                                  spec={
                                      "network": str,
                                      "subnetwork": str,
                                  }
                              ),
                              "newNetwork": arg_parsers.ArgObject(
                                  spec={
                                      "description": str,
                                      "network": str,
                                  }
                              ),
                              "newComputeNetwork": arg_parsers.ArgObject(
                                  spec={
                                      "description": str,
                                      "network": str,
                                  }
                              ),
                              "existingComputeNetwork": arg_parsers.ArgObject(
                                  spec={
                                      "network": str,
                                      "subnetwork": str,
                                  }
                              ),
                          }
                      ),
                  }
              ),
          ),
          "orchestrator": arg_parsers.ArgObject(
              spec={
                  "slurm": arg_parsers.ArgObject(
                      spec={
                          "defaultPartition": str,
                          "loginNodes": self.GetSlurmLoginNodeObject(),
                          "nodeSets": self.GetSlurmNodeSetsObject(),
                          "partitions": self.GetSlurmPartitionsObject(),
                          "prologBashScripts": arg_parsers.ArgList(),
                          "epilogBashScripts": arg_parsers.ArgList(),
                      }
                  ),
              }
          ),
          "storageResources": arg_parsers.ArgObject(
              key_type=str,
              value_type=arg_parsers.ArgObject(
                  spec={
                      "config": arg_parsers.ArgObject(
                          spec={
                              "existingBucket": arg_parsers.ArgObject(
                                  spec={"bucket": str}
                              ),
                              "existingFilestore": arg_parsers.ArgObject(
                                  spec={"filestore": str}
                              ),
                              "existingLustre": arg_parsers.ArgObject(
                                  spec={"lustre": str}
                              ),
                              "newBucket": arg_parsers.ArgObject(
                                  spec=bucket_config_beta_spec
                              ),
                              "newFilestore": arg_parsers.ArgObject(
                                  spec=FILESTORE_CONFIG_SPEC
                              ),
                              "newLustre": arg_parsers.ArgObject(
                                  spec=LUSTRE_CONFIG_SPEC
                                  | {"perUnitStorageThroughput": int}
                              ),
                          },
                      )
                  }
              ),
          ),
      }
