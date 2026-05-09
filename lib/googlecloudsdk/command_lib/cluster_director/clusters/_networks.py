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

"""Network configuration utilities for clusters command group."""

from __future__ import annotations
from typing import Any


def _GetNetworkName(args: Any, cluster_ref: Any, network: str) -> str:
  """Returns the full network name including project.

  Args:
    args: The argparse namespace.
    cluster_ref: The cluster resource reference.
    network: The network name.

  Returns:
    The full network name in format
    projects/{project}/global/networks/{network}.
  """

  project = getattr(args, "network_project", None) or (
      cluster_ref.Parent().projectsId
  )
  return f"projects/{project}/global/networks/{network}"


def _GetSubNetworkName(args: Any, cluster_ref: Any, subnetwork: str) -> str:
  """Returns the full subnetwork name including project.

  Args:
    args: The argparse namespace.
    cluster_ref: The cluster resource reference.
    subnetwork: The subnetwork name.

  Returns:
    The full subnetwork name in format projects/{project}/{subnetwork}.
  """
  project = (
      getattr(args, "network_project", None) or cluster_ref.Parent().projectsId
  )
  return f"projects/{project}/{subnetwork}"


def MakeClusterNetworks(
    args: Any, message_module: Any, cluster_ref: Any
) -> Any:
  """Makes a cluster message with network fields.

  Args:
    args: The argparse namespace.
    message_module: The API message module.
    cluster_ref: The cluster resource reference.

  Returns:
    A message_module.Cluster.NetworkResourcesValue object.
  """
  networks = message_module.Cluster.NetworkResourcesValue()
  if args.IsSpecified("create_network"):
    network_id = args.create_network.get("name")
    network_name = _GetNetworkName(args, cluster_ref, network_id)
    networks.additionalProperties.append(
        message_module.Cluster.NetworkResourcesValue.AdditionalProperty(
            key=f"net-{network_id}",
            value=message_module.NetworkResource(
                config=message_module.NetworkResourceConfig(
                    newNetwork=message_module.NewNetworkConfig(
                        network=network_name,
                        description=args.create_network.get("description"),
                    )
                )
            ),
        )
    )
  if args.IsSpecified("network") and args.IsSpecified("subnet"):
    network_id = args.network
    network_name = _GetNetworkName(args, cluster_ref, network_id)
    networks.additionalProperties.append(
        message_module.Cluster.NetworkResourcesValue.AdditionalProperty(
            key=f"net-{network_id}",
            value=message_module.NetworkResource(
                config=message_module.NetworkResourceConfig(
                    existingNetwork=message_module.ExistingNetworkConfig(
                        network=network_name,
                        subnetwork=_GetSubNetworkName(
                            args, cluster_ref, args.subnet
                        ),
                    )
                )
            ),
        )
    )
  return networks
