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


NETWORK_OBJECT = arg_parsers.ArgObject(
    spec={
        "name": str,
        "description": str,
    },
    required_keys=["name"],
    enable_shorthand=True,
    disable_key_description=True,
)

LABEL = arg_parsers.ArgObject(
    key_type=str,
    value_type=str,
    enable_shorthand=True,
    disable_key_description=True,
)

STORAGE_CONFIG = arg_parsers.ArgObject(
    spec={
        "id": str,
        "localMount": str,
    },
    required_keys=["id", "localMount"],
    repeated=True,
    disable_key_description=True,
)

EXISTING_FILESTORES_TYPE = arg_parsers.ArgObject(
    spec={
        "id": str,
        "name": str,
    },
    required_keys=["id", "name"],
    enable_shorthand=True,
    repeated=True,
    disable_key_description=True,
)

EXISTING_BUCKETS_TYPE = arg_parsers.ArgObject(
    spec={
        "id": str,
        "name": str,
    },
    required_keys=["id", "name"],
    enable_shorthand=True,
    repeated=True,
    disable_key_description=True,
)

EXISTING_LUSTRES_TYPE = arg_parsers.ArgObject(
    spec={
        "id": str,
        "name": str,
    },
    required_keys=["id", "name"],
    enable_shorthand=True,
    repeated=True,
    disable_key_description=True,
)

EXISTING_NFS_TYPE = arg_parsers.ArgObject(
    spec={
        "id": str,
        "serverIpAddress": str,
        "remoteMount": str,
        "mountOptions": str,
    },
    required_keys=["id", "serverIpAddress", "remoteMount"],
    enable_shorthand=True,
    repeated=True,
    disable_key_description=True,
)


SERVICE_ACCOUNT_TYPE = arg_parsers.ArgObject(
    spec={
        "email": str,
        "scopes": arg_parsers.ArgObject(value_type=str, repeated=True),
    }
)


class FlagTypes:
  """Generates flag types for clusters commands.

  Attributes:
    messages: The messages module for the given API version.
    is_alpha: True if the API version is v1alpha.
    is_beta: True if the API version is v1beta.
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
    self.is_beta = api_version == "v1beta"

  def GetNfsObject(self) -> arg_parsers.ArgObject:
    return EXISTING_NFS_TYPE

  def GetFilestoresObject(self) -> arg_parsers.ArgObject:
    return arg_parsers.ArgObject(
        spec={
            "id": str,
            "name": str,
            "tier": self.messages.NewFilestoreConfig.TierValueValuesEnum,
            "capacityGb": int,
            "fileshare": str,
            "protocol": (
                self.messages.NewFilestoreConfig.ProtocolValueValuesEnum
            ),
            "description": str,
        },
        required_keys=["id", "name", "tier", "capacityGb", "fileshare"],
        enable_shorthand=True,
        repeated=True,
        disable_key_description=True,
    )

  def GetCreateLustresObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing Lustre configurations."""

    spec = {
        "id": str,
        "name": str,
        "filesystem": str,
        "capacityGb": int,
        "description": str,
        "perUnitStorageThroughput": int,
    }
    if self.is_alpha:
      spec["dynamicTierOptionsMode"] = arg_parsers.ArgObject(
          value_type=self.messages.DynamicTierOptions.ModeValueValuesEnum,
          help_text=(
              "Sets dynamicTierOptionsMode value. "
              "Allowed values: DISABLED, DEFAULT_CACHE."
          ),
      )
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["id", "name", "capacityGb", "filesystem"],
        repeated=True,
        enable_shorthand=True,
        disable_key_description=True,
    )

  def GetProtoBootDiskType(self) -> arg_parsers.ArgObject:
    spec = {
        "type": str,
        "sizeGb": int,
    }
    if self.is_alpha:
      spec["image"] = str
      spec["storagePools"] = arg_parsers.ArgObject(
          value_type=str, repeated=True
      )
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["type", "sizeGb"],
        enable_shorthand=True,
        disable_key_description=True,
    )

  def GetGcsBucketsObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing GCS bucket configurations."""

    spec = {
        "id": str,
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
        required_keys=["id", "name"],
        enable_shorthand=True,
        repeated=True,
        disable_key_description=True,
    )

  def GetOnDemandInstancesObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing on demand instance configurations."""
    spec = {
        "id": str,
        "zone": str,
        "machineType": str,
    }
    if self.is_alpha or self.is_beta:
      spec["networkTags"] = arg_parsers.ArgObject(
          value_type=str, repeated=True
      )
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["id", "zone", "machineType"],
        enable_shorthand=True,
        repeated=True,
        disable_key_description=True,
    )

  def GetSpotInstancesObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing spot instance configurations."""
    spec = {
        "id": str,
        "zone": str,
        "machineType": str,
        "terminationAction": (
            self.messages.NewSpotInstancesConfig.TerminationActionValueValuesEnum
        ),
    }
    if self.is_alpha or self.is_beta:
      spec["networkTags"] = arg_parsers.ArgObject(
          value_type=str, repeated=True
      )
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["id", "zone", "machineType"],
        enable_shorthand=True,
        repeated=True,
        disable_key_description=True,
    )

  def GetReservedInstancesObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing reserved instance configurations."""
    spec = {
        "id": str,
        "reservation": str,
    }
    if self.is_alpha or self.is_beta:
      spec["networkTags"] = arg_parsers.ArgObject(
          value_type=str, repeated=True
      )
    if self.is_alpha:
      spec.update({
          "reservationBlock": str,
          "reservationSubBlock": str,
      })
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["id"],
        enable_shorthand=True,
        repeated=True,
        disable_key_description=True,
    )

  def GetFlexStartInstancesObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing flex start instance configurations."""
    spec = {
        "id": str,
        "zone": str,
        "machineType": str,
        "maxDuration": str,
    }
    if self.is_alpha or self.is_beta:
      spec["networkTags"] = arg_parsers.ArgObject(
          value_type=str, repeated=True
      )
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["id", "zone", "machineType", "maxDuration"],
        enable_shorthand=True,
        repeated=True,
        disable_key_description=True,
    )

  def _GetSlurmNodeConfigSpec(self) -> dict[str, Any]:
    return {
        "cpuSpecList": str,
        "features": str,
        "memSpecLimit": str,
        "weight": str,
        "coreSpecCount": str,
    }

  def GetSlurmNodeSetsObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing Slurm Node Sets configurations."""
    if self.is_alpha:
      return arg_parsers.ArgObject(
          spec={
              "id": str,
              "computeId": str,
              "staticNodeCount": int,
              "maxDynamicNodeCount": int,
              "config": arg_parsers.ArgObject(
                  spec=self._GetSlurmNodeConfigSpec(),
                  enable_shorthand=True,
              ),
              "computeInstance": arg_parsers.ArgObject(
                  spec={
                      "startupScript": str,
                      "labels": LABEL,
                      "bootDisk": self.GetProtoBootDiskType(),
                      "startupScriptTimeout": str,
                  },
                  enable_shorthand=True,
              ),
              "containerNodePool": arg_parsers.ArgObject(
                  spec={
                      "resourceLabels": LABEL,
                      "startupScript": str,
                  },
                  enable_shorthand=True,
              ),
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
          disable_key_description=True,
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
          disable_key_description=True,
      )

  def _GetSlurmPartitionConfigSpec(self) -> dict[str, Any]:
    return {
        "defMemPerCpu": str,
        "maxNodes": str,
        "overSubscribe": str,
        "priorityTier": str,
        "priorityJobFactor": str,
        "allowAccounts": str,
        "allowQos": str,
        "denyAccounts": str,
        "denyQos": str,
        "exclusiveUser": str,
        "qos": str,
        "tresBillingWeights": str,
        "graceTime": str,
        "defaultTime": str,
        "maxTime": str,
        "overTimeLimit": str,
        "preemptMode": str,
    }

  def _GetSlurmPartitionSpec(self) -> dict[str, Any]:
    spec = {
        "id": str,
        "nodeSetIds": arg_parsers.ArgObject(value_type=str, repeated=True),
    }
    if self.is_alpha:
      spec["config"] = arg_parsers.ArgObject(
          spec=self._GetSlurmPartitionConfigSpec(),
          enable_shorthand=True,
          disable_key_description=True,
      )
    return spec

  def GetSlurmPartitionsObject(self) -> arg_parsers.ArgObject:
    return arg_parsers.ArgObject(
        spec=self._GetSlurmPartitionSpec(),
        required_keys=["id", "nodeSetIds"],
        enable_shorthand=True,
        repeated=True,
        disable_key_description=True,
    )

  def GetSlurmPartitionsUpdateObject(self) -> arg_parsers.ArgObject:
    return arg_parsers.ArgObject(
        spec=self._GetSlurmPartitionSpec(),
        required_keys=["id"],
        enable_shorthand=True,
        repeated=True,
        disable_key_description=True,
    )

  def _GetManagedInstanceGroupSpec(self) -> dict[str, Any]:
    return {
        "id": str,
        "computeId": str,
        "targetSize": int,
        "acceleratorTopology": str,
        "enablePublicIps": bool,
        "startupScript": arg_parsers.ArgObject(),
        "bootDisk": self.GetProtoBootDiskType(),
        "storageConfigs": STORAGE_CONFIG,
    }

  def GetManagedInstanceGroupsObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing Managed Instance Group configs."""
    spec = self._GetManagedInstanceGroupSpec()
    spec["serviceAccount"] = SERVICE_ACCOUNT_TYPE
    return arg_parsers.ArgObject(
        spec=spec,
        required_keys=["id", "computeId"],
        enable_shorthand=True,
        repeated=True,
        disable_key_description=True,
    )

  def GetManagedInstanceGroupsUpdateObject(self) -> arg_parsers.ArgObject:
    """Returns an ArgObject for parsing Managed Instance Group updates."""
    return arg_parsers.ArgObject(
        spec=self._GetManagedInstanceGroupSpec(),
        required_keys=["id"],
        enable_shorthand=True,
        repeated=True,
        disable_key_description=True,
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
              "networkTags": arg_parsers.ArgObject(
                  value_type=str, repeated=True
              ),
          },
          required_keys=["machineType", "zone"],
          enable_shorthand=True,
          disable_key_description=True,
      )
    else:
      spec = {
          "machineType": str,
          "zone": str,
          "count": int,
          "enableOsLogin": bool,
          "enablePublicIps": bool,
          "startupScript": str,
          "labels": LABEL,
          "bootDisk": self.GetProtoBootDiskType(),
          "storageConfigs": STORAGE_CONFIG,
      }
      if self.is_beta:
        spec["networkTags"] = arg_parsers.ArgObject(
            value_type=str, repeated=True
        )
      return arg_parsers.ArgObject(
          spec=spec,
          required_keys=["machineType", "zone"],
          enable_shorthand=True,
          disable_key_description=True,
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
          disable_key_description=True,
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
          disable_key_description=True,
      )
