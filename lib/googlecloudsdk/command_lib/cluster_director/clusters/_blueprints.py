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

"""Baseline blueprint and quickstart configuration definitions for creation."""

from __future__ import annotations

from typing import Any, Dict, Optional, cast
import uuid

from googlecloudsdk.command_lib.cluster_director.clusters import errors

BLUEPRINT_DEFINITIONS = {
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
                        "filesystem": "scratch-fs",
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
                        "filesystem": "scratch-fs",
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
                        "filesystem": "scratch-fs",
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
                        "filesystem": "scratch-fs",
                    }
                }
            }
        },
    },
    "g4": {
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
                        "filesystem": "scratch-fs",
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
    "h4d-highmem": {
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
                        "filesystem": "scratch-fs",
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


def ApplyBlueprint(
    args: Any, message_module: Any, cluster_ref: Any
) -> None:
  """Applies blueprint or quickstart defaults to arguments."""
  blueprint = getattr(args, "blueprint", None)
  quickstart = getattr(args, "quickstart_cluster", False)
  if not blueprint and not quickstart:
    return

  if blueprint and quickstart:
    raise errors.ClusterDirectorError(
        "Cannot specify both --blueprint and --quickstart-cluster."
    )

  if quickstart:
    blueprint_spec = BLUEPRINT_DEFINITIONS.get("quickstart")
    label = "--quickstart-cluster"
  else:
    blueprint_spec = cast(Dict[str, Any], BLUEPRINT_DEFINITIONS.get(blueprint))
    label = f"'{blueprint}'"

  if not blueprint_spec:
    raise errors.ClusterDirectorError(
        f"Blueprint {label} is not defined."
    )

  _ApplySpec(args, message_module, cluster_ref, blueprint_spec, label)


def _ApplySpec(
    args: Any,
    message_module: Any,
    cluster_ref: Any,
    spec: Dict[str, Any],
    label: str,
) -> None:
  """Applies dynamic defaults from a spec dictionary to argparse args namespace."""
  prefix = cluster_ref.clustersId
  zone = f"{cluster_ref.locationsId}-b"  # Default zone if not specified.
  ri_zone = zone
  compute_id = f"{prefix}-compute"

  # 1. Process Compute Resources from Spec
  compute_resources = spec.get("computeResources", {})
  if compute_resources:
    # Get the first compute config
    _, resource_spec = list(compute_resources.items())[0]
    config_spec = resource_spec.get("config", {})

    if "newReservedInstances" in config_spec:
      if not args.IsSpecified("reserved_instances"):
        raise errors.ClusterDirectorError(
            f"Blueprint {label} requires a reservation. Please specify "
            "the --reserved-instances flag with a valid reservation."
        )
      for ri in args.reserved_instances:
        if not (
            ri.get("reservation")
            or ri.get("reservationBlock")
            or ri.get("reservationSubBlock")
        ):
          raise errors.ClusterDirectorError(
              f"Blueprint {label} requires a reservation. Please specify a"
              " reservation, reservationBlock, or reservationSubBlock in"
              " --reserved-instances."
          )
        res_path = ri.get("reservation")
        inferred_zone = None
        if res_path:
          inferred_zone = _GetZoneFromReservation(res_path)

        ri_zone = inferred_zone or zone
        if not ri.get("zone"):
          ri["zone"] = ri_zone

      compute_id = (
          args.reserved_instances[0].get("id")
          if args.reserved_instances
          else f"{prefix}-compute"
      )
      ri_zone = (
          args.reserved_instances[0].get("zone")
          if args.reserved_instances
          else zone
      )

    elif "newFlexStartInstances" in config_spec:
      spec_flex = config_spec["newFlexStartInstances"]
      if not args.IsSpecified("flex_start_instances"):
        args.flex_start_instances = [{
            "id": f"{prefix}-compute",
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

      compute_id = (
          args.flex_start_instances[0].get("id")
          if args.flex_start_instances
          else f"{prefix}-compute"
      )
      ri_zone = (
          args.flex_start_instances[0].get("zone")
          if args.flex_start_instances
          else zone
      )

  # 2. Process Storage Resources from Spec
  storage_resources = spec.get("storageResources", {})
  for _, storage_spec in storage_resources.items():
    st_config = storage_spec.get("config", {})
    if "newLustre" in st_config:
      spec_lustre = st_config["newLustre"]
      if not args.IsSpecified("create_lustres"):
        args.create_lustres = [{
            "id": f"{prefix}-scratch-disk",
            "name": f"locations/{ri_zone}/instances/{prefix}-lustre",
            "capacityGb": spec_lustre["capacityGb"],
            "perUnitStorageThroughput": spec_lustre["perUnitStorageThroughput"],
            "filesystem": f"{prefix}fs",
        }]
        _SetSpecified(args, "create_lustres", "--create-lustres")

    elif "newFilestore" in st_config:
      spec_filestore = st_config["newFilestore"]
      if not args.IsSpecified("create_filestores"):
        tier_enum = message_module.NewFilestoreConfig.TierValueValuesEnum(
            spec_filestore["tier"]
        )
        fileshare_spec = spec_filestore.get("fileShares", [{}])[0]
        args.create_filestores = [{
            "id": f"{prefix}-filestore-disk",
            "name": f"locations/{ri_zone}/instances/{prefix}-filestore",
            "capacityGb": fileshare_spec.get("capacityGb"),
            "fileshare": fileshare_spec.get("fileShare"),
            "tier": tier_enum,
        }]
        _SetSpecified(args, "create_filestores", "--create-filestores")

  # 3. Create Network if not specified
  if not args.IsSpecified("network") and not args.IsSpecified("create_network"):
    random_suffix = uuid.uuid4().hex[:5]
    args.create_network = {"name": f"{prefix}-net-{random_suffix}"}
    _SetSpecified(args, "create_network", "--create-network")

  # 4. Create Node Sets and Partitions
  node_count = spec.get("nodeCount", 1)
  if not args.IsSpecified("slurm_node_sets"):
    args.slurm_node_sets = [{
        "id": f"{prefix}ns",
        "computeId": compute_id,
        "type": "gce",
        "staticNodeCount": node_count,
    }]
    _SetSpecified(args, "slurm_node_sets", "--slurm-node-sets")
  if not args.IsSpecified("slurm_partitions"):
    args.slurm_partitions = [{
        "id": f"{prefix}partition",
        "nodeSetIds": [f"{prefix}ns"],
    }]
    _SetSpecified(args, "slurm_partitions", "--slurm-partitions")
  if not args.IsSpecified("slurm_default_partition"):
    args.slurm_default_partition = f"{prefix}partition"
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
