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

"""Baseline reference architecture and quickstart configuration definitions for creation."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, cast
import uuid

from googlecloudsdk.command_lib.cluster_director.clusters import errors

REFERENCE_ARCHITECTURE_DEFINITIONS = {
    "quickstart": {
        "computeResources": {
            "quickstart-fleet": {
                "config": {
                    "newFlexStartInstances": {
                        "machineType": "a3-megagpu-8g",
                        "maxDuration": "604800s",
                    }
                }
            }
        },
        "nodeCount": 2,
        "loginNode": {"machineType": "n2-standard-16", "count": 1},
        "storageResources": {
            "scratch-disk": {
                "config": {
                    "newLustre": {
                        "capacityGb": 36000,
                        "perUnitStorageThroughput": 500,
                        "filesystem": "scratch",
                    }
                }
            }
        },
    },
    "a3-ultra": {
        "computeResources": {
            "a3-ultra-fleet": {"config": {"newReservedInstances": {}}}
        },
        "nodeCount": 4,
        "loginNode": {"machineType": "n2-standard-16", "count": 1},
        "storageResources": {
            "scratch-disk": {
                "config": {
                    "newLustre": {
                        "capacityGb": 36000,
                        "perUnitStorageThroughput": 500,
                        "filesystem": "scratch",
                    }
                }
            },
            "filestore-disk": {
                "config": {
                    "newFilestore": {
                        "tier": "ZONAL",
                        "fileShares": [
                            {"capacityGb": 5120, "fileShare": "nfsshare"}
                        ],
                    }
                }
            },
        },
    },
    "a4-high-flex-start": {
        "computeResources": {
            "a4-fleet": {
                "config": {
                    "newFlexStartInstances": {
                        "machineType": "a4-highgpu-8g",
                        "maxDuration": "604800s",
                    }
                }
            }
        },
        "nodeCount": 4,
        "loginNode": {"machineType": "n2-standard-16", "count": 1},
        "storageResources": {
            "scratch-disk": {
                "config": {
                    "newLustre": {
                        "capacityGb": 18000,
                        "perUnitStorageThroughput": 500,
                        "filesystem": "scratch",
                    }
                }
            },
            "filestore-disk": {
                "config": {
                    "newFilestore": {
                        "tier": "ZONAL",
                        "fileShares": [
                            {"capacityGb": 2048, "fileShare": "nfsshare"}
                        ],
                    }
                }
            },
        },
    },
    "a4x-high": {
        "computeResources": {
            "a4x-fleet": {"config": {"newReservedInstances": {}}}
        },
        "nodeCount": 18,
        "loginNode": {"machineType": "n2-standard-16", "count": 1},
        "storageResources": {
            "scratch-disk": {
                "config": {
                    "newLustre": {
                        "capacityGb": 36000,
                        "perUnitStorageThroughput": 1000,
                        "filesystem": "scratch",
                    }
                }
            }
        },
    },
    "g4-flex-start": {
        "computeResources": {
            "g4-fleet": {
                "config": {
                    "newFlexStartInstances": {
                        "machineType": "g4-standard-384",
                        "maxDuration": "604800s",
                    }
                }
            }
        },
        "nodeCount": 4,
        "loginNode": {"machineType": "n2-standard-16", "count": 1},
        "storageResources": {
            "scratch-disk": {
                "config": {
                    "newLustre": {
                        "capacityGb": 36000,
                        "perUnitStorageThroughput": 500,
                        "filesystem": "scratch",
                    }
                }
            },
            "filestore-disk": {
                "config": {
                    "newFilestore": {
                        "tier": "ZONAL",
                        "fileShares": [
                            {"capacityGb": 10240, "fileShare": "nfsshare"}
                        ],
                    }
                }
            },
        },
    },
    "h4d-highmem-flex-start": {
        "computeResources": {
            "h4d-fleet": {
                "config": {
                    "newFlexStartInstances": {
                        "machineType": "h4d-highmem-192",
                        "maxDuration": "604800s",
                    }
                }
            }
        },
        "nodeCount": 4,
        "loginNode": {"machineType": "n2-standard-16", "count": 1},
        "storageResources": {
            "scratch-disk": {
                "config": {
                    "newLustre": {
                        "capacityGb": 18000,
                        "perUnitStorageThroughput": 500,
                        "filesystem": "scratch",
                    }
                }
            },
            "filestore-disk": {
                "config": {
                    "newFilestore": {
                        "tier": "ZONAL",
                        "fileShares": [
                            {"capacityGb": 1024, "fileShare": "nfsshare"}
                        ],
                    }
                }
            },
        },
    },
}


def ApplyReferenceArchitecture(
    args: Any, message_module: Any, cluster_ref: Any
) -> None:
  """Applies reference architecture or quickstart defaults to arguments."""
  ref_arch = getattr(args, "reference_architecture", None)
  quickstart = getattr(args, "quickstart_cluster", False)
  if not ref_arch and not quickstart:
    return

  if ref_arch and quickstart:
    raise errors.ClusterDirectorError(
        "Cannot specify both --reference-architecture and --quickstart-cluster."
    )

  if quickstart:
    spec = REFERENCE_ARCHITECTURE_DEFINITIONS.get("quickstart")
    label = "--quickstart-cluster"
  else:
    spec = cast(
        Dict[str, Any], REFERENCE_ARCHITECTURE_DEFINITIONS.get(ref_arch)
    )
    label = f"'{ref_arch}'"

  if not spec:
    raise errors.ClusterDirectorError(
        f"Reference architecture {label} is not defined."
    )

  _ApplySpec(args, message_module, cluster_ref, spec, label)


def _GetSpecifiedZone(args: Any) -> Optional[str]:
  """Returns the first specified zone from compute instances in args."""
  for flag in [
      "on_demand_instances",
      "spot_instances",
      "reserved_instances",
      "flex_start_instances",
  ]:
    if args.IsSpecified(flag):
      instances = getattr(args, flag)
      for instance in instances:
        if instance.get("zone"):
          return instance.get("zone")
  return None


def _SafeAppend(prefix: str, suffix: str, max_length: int = 63) -> str:
  """Appends suffix to prefix, truncating prefix to fit max_length."""
  if len(prefix) + len(suffix) <= max_length:
    return prefix + suffix

  truncate_to = max_length - len(suffix)
  truncated = prefix[:truncate_to]

  # Avoid double dashes if both truncated ends with '-' and
  # suffix starts with '-'
  if truncated.endswith("-") and suffix.startswith("-"):
    truncated = truncated[:-1]

  return truncated + suffix


def _GetSpecifiedComputeResources(args: Any) -> Dict[str, List[Any]]:
  """Returns a dict of specified compute resources by flag name."""
  specified = {}
  for flag in [
      "flex_start_instances",
      "on_demand_instances",
      "spot_instances",
      "reserved_instances",
  ]:
    if args.IsSpecified(flag):
      specified[flag] = getattr(args, flag)
  return specified


def _ApplySpec(
    args: Any,
    message_module: Any,
    cluster_ref: Any,
    spec: Dict[str, Any],
    label: str,
) -> None:
  """Applies dynamic defaults from a spec dictionary to argparse args namespace."""
  prefix = cluster_ref.clustersId
  specified_zone = _GetSpecifiedZone(args)
  zone = (
      specified_zone or f"{cluster_ref.locationsId}-b"
  )  # Default zone if not specified.
  ri_zone = zone
  default_compute_id = _SafeAppend(prefix, "-compute")

  # 1. Process Compute Resources from Spec
  compute_resources = spec.get("computeResources", {})
  expected_type = None
  spec_config = {}
  if compute_resources:
    _, resource_spec = list(compute_resources.items())[0]
    spec_config = resource_spec.get("config", {})
    if "newReservedInstances" in spec_config:
      expected_type = "reserved_instances"
    elif "newFlexStartInstances" in spec_config:
      expected_type = "flex_start_instances"

  specified_computes = _GetSpecifiedComputeResources(args)

  should_apply_default = False
  if not specified_computes:
    should_apply_default = True
  elif expected_type in specified_computes:
    should_apply_default = True

  if should_apply_default and expected_type:
    if expected_type == "reserved_instances":
      if not args.IsSpecified("reserved_instances"):
        raise errors.ClusterDirectorError(
            f"Reference architecture {label} requires a reservation. Please"
            " specify the --reserved-instances flag with a valid reservation."
        )
      for ri in args.reserved_instances:
        if not (
            ri.get("reservation")
            or ri.get("reservationBlock")
            or ri.get("reservationSubBlock")
        ):
          raise errors.ClusterDirectorError(
              f"Reference architecture {label} requires a reservation. Please"
              " specify a reservation, reservationBlock, or"
              " reservationSubBlock in --reserved-instances."
          )
        res_path = ri.get("reservation")
        inferred_zone = None
        if res_path:
          inferred_zone = _GetZoneFromReservation(res_path)

        ri_zone = inferred_zone or zone
        if not ri.get("zone"):
          ri["zone"] = ri_zone
      ri_zone = (
          args.reserved_instances[0].get("zone")
          if args.reserved_instances
          else zone
      )

    elif expected_type == "flex_start_instances":
      spec_flex = spec_config["newFlexStartInstances"]
      if not args.IsSpecified("flex_start_instances"):
        args.flex_start_instances = [{
            "id": default_compute_id,
            "machineType": spec_flex["machineType"],
            "zone": zone,
            "maxDuration": spec_flex["maxDuration"],
        }]
        _SetSpecified(args, "flex_start_instances", "--flex-start-instances")
      else:
        for fsi in args.flex_start_instances:
          if not fsi.get("machineType"):
            fsi["machineType"] = spec_flex["machineType"]
          if not fsi.get("zone"):
            fsi["zone"] = zone
          if not fsi.get("maxDuration"):
            fsi["maxDuration"] = spec_flex["maxDuration"]

      ri_zone = (
          args.flex_start_instances[0].get("zone")
          if args.flex_start_instances
          else zone
      )
  else:
    # User specified other compute, don't apply defaults from spec.
    # Just resolve compute_id and ri_zone from what they specified.
    primary_type = None
    primary_compute = None
    for flag in [
        "flex_start_instances",
        "reserved_instances",
        "spot_instances",
        "on_demand_instances",
    ]:
      if flag in specified_computes:
        primary_compute = specified_computes[flag][0]
        primary_type = flag
        break

    if primary_compute:
      if primary_type == "reserved_instances":
        res_path = primary_compute.get("reservation")
        inferred_zone = None
        if res_path:
          inferred_zone = _GetZoneFromReservation(res_path)
        ri_zone = inferred_zone or zone
        if not primary_compute.get("zone"):
          primary_compute["zone"] = ri_zone
      else:
        ri_zone = primary_compute.get("zone") or zone

  # 2. Process Storage Resources from Spec
  storage_resources = spec.get("storageResources", {})
  for _, storage_spec in storage_resources.items():
    st_config = storage_spec.get("config", {})
    if "newLustre" in st_config:
      spec_lustre = st_config["newLustre"]
      if not args.IsSpecified("create_lustres"):
        lustre_id = _SafeAppend(prefix, "-lustre")
        # Sanitize prefix for filesystem name: only alphanumeric, lowercase,
        # max 6 chars (to leave 2 for 'fs').
        sanitized_prefix = re.sub(r"[^a-zA-Z0-9]", "", prefix).lower()
        fs_name = sanitized_prefix[:6] + "fs"
        args.create_lustres = [{
            "id": _SafeAppend(prefix, "-scratch-disk"),
            "name": f"locations/{ri_zone}/instances/{lustre_id}",
            "capacityGb": spec_lustre["capacityGb"],
            "perUnitStorageThroughput": spec_lustre["perUnitStorageThroughput"],
            "filesystem": fs_name,
        }]
        _SetSpecified(args, "create_lustres", "--create-lustres")

    elif "newFilestore" in st_config:
      spec_filestore = st_config["newFilestore"]
      if not args.IsSpecified("create_filestores"):
        tier_enum = message_module.NewFilestoreConfig.TierValueValuesEnum(
            spec_filestore["tier"]
        )
        fileshare_spec = spec_filestore.get("fileShares", [{}])[0]
        filestore_id = _SafeAppend(prefix, "-filestore")
        args.create_filestores = [{
            "id": _SafeAppend(prefix, "-filestore-disk"),
            "name": f"locations/{ri_zone}/instances/{filestore_id}",
            "capacityGb": fileshare_spec.get("capacityGb"),
            "fileshare": fileshare_spec.get("fileShare"),
            "tier": tier_enum,
        }]
        _SetSpecified(args, "create_filestores", "--create-filestores")

  # 3. Create Network if not specified
  if not args.IsSpecified("network") and not args.IsSpecified("create_network"):
    random_suffix = uuid.uuid4().hex[:5]
    net_name = _SafeAppend(prefix, f"-net-{random_suffix}")
    args.create_network = {"name": net_name}
    _SetSpecified(args, "create_network", "--create-network")

  # 4. Create Node Sets and Partitions
  if not args.IsSpecified("slurm_node_sets"):
    defined_computes = []
    for flag in [
        "flex_start_instances",
        "reserved_instances",
        "spot_instances",
        "on_demand_instances",
    ]:
      if args.IsSpecified(flag) or getattr(args, flag, None):
        for comp in getattr(args, flag, None) or []:
          defined_computes.append((comp, flag == "flex_start_instances"))

    args.slurm_node_sets = []
    for i, (comp, is_comp_flex) in enumerate(defined_computes):
      comp_id = comp.get("id")
      if len(defined_computes) == 1:
        ns_id = _SafeAppend(prefix, "ns")
      else:
        ns_id = _SafeAppend(prefix, f"ns{i}")

      node_set = {
          "id": ns_id,
          "computeId": comp_id,
          "type": "gce",
      }
      count = spec.get("nodeCount", 1) if i == 0 else 1
      machine_type = comp.get("machineType")
      is_tpu = machine_type and machine_type.startswith(("ct", "tpu"))
      if is_comp_flex or is_tpu:
        node_set["maxDynamicNodeCount"] = count
      else:
        node_set["staticNodeCount"] = count
      args.slurm_node_sets.append(node_set)
    _SetSpecified(args, "slurm_node_sets", "--slurm-node-sets")

  if not args.IsSpecified("slurm_partitions"):
    partition_id = _SafeAppend(prefix, "partition")
    node_set_ids = [ns["id"] for ns in args.slurm_node_sets]
    args.slurm_partitions = [{
        "id": partition_id,
        "nodeSetIds": node_set_ids,
    }]
    _SetSpecified(args, "slurm_partitions", "--slurm-partitions")
  if not args.IsSpecified("slurm_default_partition"):
    args.slurm_default_partition = _SafeAppend(prefix, "partition")
    _SetSpecified(args, "slurm_default_partition", "--slurm-default-partition")

  # 5. Default Login Nodes
  login_node_spec = spec.get("loginNode", {})
  if login_node_spec and not args.IsSpecified("slurm_login_node"):
    args.slurm_login_node = {
        "machineType": login_node_spec.get("machineType"),
        "count": login_node_spec.get("count"),
        "zone": ri_zone,
    }
    _SetSpecified(args, "slurm_login_node", "--slurm-login-node")


def _GetZoneFromReservation(reservation: str) -> Optional[str]:
  parts = reservation.split("/")
  try:
    idx = parts.index("zones")
    if idx + 1 < len(parts):
      return parts[idx + 1]
  except ValueError:
    pass
  return None


def _SetSpecified(args: Any, dest: str, flag_name: str) -> None:
  if hasattr(args, "_specified_args"):
    args._specified_args[dest] = flag_name  # pylint: disable=protected-access
