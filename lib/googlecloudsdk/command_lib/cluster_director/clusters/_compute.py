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

"""Compute configuration utilities for clusters command group."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSet, Sequence
from typing import Any

from googlecloudsdk.command_lib.cluster_director.clusters import errors

ClusterDirectorError = errors.ClusterDirectorError

# Error messages
_COMPUTE_INSTANCE_ALREADY_EXISTS_ERROR = (
    "Compute instances with id={id} already exist."
)
_COMPUTE_INSTANCE_NOT_FOUND_ERROR = "Compute instances with id={id} not found."


def _GetReservationZone(reservation: str) -> str:
  """Returns the reservation zone from a reservation resource string.

  Args:
    reservation: The reservation resource string.

  Returns:
    The zone extracted from the reservation string.

  Raises:
    ClusterDirectorError: If the reservation string does not contain a zone.
  """

  # projects/{project}/zones/{zone}/reservations/{reservation}/reservationBlocks/{reservationBlock}
  parts = reservation.split("/")
  for current_part, next_part in zip(parts, parts[1:]):
    if current_part == "zones" and next_part:
      return next_part
  raise ClusterDirectorError(
      f"Reservation {reservation} does not contain a zone."
  )


def _GetReservationName(cluster_ref: Any, reservation: str) -> str:
  """Returns the full reservation name including project.

  Args:
    cluster_ref: The cluster resource reference.
    reservation: The reservation string, which may or may not include
      'projects/'.

  Returns:
    The full reservation name.

  Raises:
    ClusterDirectorError: If the reservation string does not contain a zone.
  """
  project = cluster_ref.Parent().projectsId
  if reservation.startswith("projects/"):
    reservation_name = reservation
  else:
    reservation_name = f"projects/{project}/{reservation}"
  _GetReservationZone(reservation)
  return reservation_name


def _MakeOnDemandComputeResource(
    message_module: Any, instance: Mapping[str, Any]
) -> Any:
  """Makes a cluster compute resource message for on demand instances.

  Args:
    message_module: The API message module.
    instance: A dictionary containing on-demand instance configuration.

  Returns:
    A message_module.ComputeResource object for on-demand instances.
  """
  return message_module.ComputeResource(
      config=message_module.ComputeResourceConfig(
          newOnDemandInstances=message_module.NewOnDemandInstancesConfig(
              zone=instance.get("zone"),
              machineType=instance.get("machineType"),
          ),
      ),
  )


def _MakeSpotComputeResource(
    message_module: Any, instance: Mapping[str, Any]
) -> Any:
  """Makes a cluster compute resource message for spot instances.

  Args:
    message_module: The API message module.
    instance: A dictionary containing spot instance configuration.

  Returns:
    A message_module.ComputeResource object for spot instances.
  """
  return message_module.ComputeResource(
      config=message_module.ComputeResourceConfig(
          newSpotInstances=message_module.NewSpotInstancesConfig(
              zone=instance.get("zone"),
              machineType=instance.get("machineType"),
              terminationAction=instance.get("terminationAction"),
          ),
      ),
  )


def _MakeReservedComputeResource(
    message_module: Any, cluster_ref: Any, instance: Mapping[str, Any]
) -> Any:
  """Makes a cluster compute resource message for reserved instances.

  Args:
    message_module: The API message module.
    cluster_ref: The cluster resource reference.
    instance: A dictionary containing reserved instance configuration.

  Returns:
    A message_module.ComputeResource object for reserved instances.

  Raises:
    ClusterDirectorError: If not exactly one of reservation, reservationBlock,
      or reservationSubBlock is provided.
  """
  reservation = instance.get("reservation")
  reservation_block = instance.get("reservationBlock")
  reservation_sub_block = instance.get("reservationSubBlock")
  if (
      sum(
          p is not None
          for p in [reservation, reservation_block, reservation_sub_block]
      )
      != 1
  ):
    raise ClusterDirectorError(
        "Exactly one of reservation, reservationBlock, or"
        " reservationSubBlock must be provided for reserved instances."
    )
  if reservation:
    return message_module.ComputeResource(
        config=message_module.ComputeResourceConfig(
            newReservedInstances=message_module.NewReservedInstancesConfig(
                reservation=_GetReservationName(cluster_ref, reservation),
            ),
        ),
    )
  elif reservation_block:
    return message_module.ComputeResource(
        config=message_module.ComputeResourceConfig(
            newReservedInstances=message_module.NewReservedInstancesConfig(
                reservationBlock=_GetReservationName(
                    cluster_ref, reservation_block
                ),
            ),
        ),
    )
  else:
    return message_module.ComputeResource(
        config=message_module.ComputeResourceConfig(
            newReservedInstances=message_module.NewReservedInstancesConfig(
                reservationSubBlock=_GetReservationName(
                    cluster_ref, reservation_sub_block
                ),
            ),
        ),
    )


def _MakeFlexStartComputeResource(
    message_module: Any, instance: Mapping[str, Any]
) -> Any:
  """Makes a cluster compute resource message for flex start instances.

  Args:
    message_module: The API message module.
    instance: A dictionary containing flex start instance configuration.

  Returns:
    A message_module.ComputeResource object for flex start instances.
  """
  return message_module.ComputeResource(
      config=message_module.ComputeResourceConfig(
          newFlexStartInstances=message_module.NewFlexStartInstancesConfig(
              zone=instance.get("zone"),
              machineType=instance.get("machineType"),
              maxDuration=instance.get("maxDuration"),
          ),
      ),
  )


def MakeClusterCompute(args: Any, message_module: Any, cluster_ref: Any) -> Any:
  """Makes a cluster message with compute fields.

  Args:
    args: The argparse namespace.
    message_module: The API message module.
    cluster_ref: The cluster resource reference.

  Returns:
    A message_module.Cluster.ComputeResourcesValue object.

  Raises:
    ClusterDirectorError: If no compute instances are specified, or if
      duplicate compute instance ids are provided.
  """
  if (
      not args.IsSpecified("on_demand_instances")
      and not args.IsSpecified("spot_instances")
      and not args.IsSpecified("reserved_instances")
      and not args.IsSpecified("flex_start_instances")
  ):
    raise ClusterDirectorError(
        "At least one of on_demand_instances, spot_instances,"
        " reserved_instances, or flex_start_instances flag must be specified."
    )
  compute_ids = set()
  compute = message_module.Cluster.ComputeResourcesValue()
  if args.IsSpecified("on_demand_instances"):
    for instance in args.on_demand_instances:
      compute_id = instance.get("id")
      compute_ids.add(compute_id)
      compute.additionalProperties.append(
          message_module.Cluster.ComputeResourcesValue.AdditionalProperty(
              key=compute_id,
              value=_MakeOnDemandComputeResource(message_module, instance),
          )
      )
  if args.IsSpecified("spot_instances"):
    for instance in args.spot_instances:
      compute_id = instance.get("id")
      compute_ids.add(compute_id)
      compute.additionalProperties.append(
          message_module.Cluster.ComputeResourcesValue.AdditionalProperty(
              key=compute_id,
              value=_MakeSpotComputeResource(message_module, instance),
          )
      )
  if args.IsSpecified("reserved_instances"):
    for instance in args.reserved_instances:
      compute_id = instance.get("id")
      compute_ids.add(compute_id)
      compute.additionalProperties.append(
          message_module.Cluster.ComputeResourcesValue.AdditionalProperty(
              key=compute_id,
              value=_MakeReservedComputeResource(
                  message_module, cluster_ref, instance
              ),
          )
      )
  if args.IsSpecified("flex_start_instances"):
    for instance in args.flex_start_instances:
      compute_id = instance.get("id")
      compute_ids.add(compute_id)
      compute.additionalProperties.append(
          message_module.Cluster.ComputeResourcesValue.AdditionalProperty(
              key=compute_id,
              value=_MakeFlexStartComputeResource(message_module, instance),
          )
      )
  if len(compute_ids) != len(compute.additionalProperties):
    raise ClusterDirectorError(
        "Compute instances with duplicate ids are not supported."
    )
  return compute


def _ConvertMessageToDict(message: Any) -> dict[str, Any]:
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


def _AddKeyToDictSpec(
    key: str,
    dict_spec: MutableMapping[str, Any],
    value: Any,
    exception_message: str,
) -> None:
  """Adds a cluster identifier (key) with value, if not present in dict spec.

  Args:
    key: The key to add.
    dict_spec: The dictionary to add to.
    value: The value to add for the key.
    exception_message: The exception message template to use if key exists.

  Raises:
    ClusterDirectorError: If key is already in dict_spec.
  """
  if key in dict_spec:
    raise ClusterDirectorError(exception_message.format(id=key))
  dict_spec[key] = value


def _RemoveKeyByAttrFromDictSpec(
    key: str,
    dict_spec: MutableMapping[str, Any],
    attrs: Sequence[str],
    key_exception_message: str,
    attr_exception_message: str,
) -> None:
  """Removes a cluster identifier (key) by attribute, if present in dict spec.

  Checks if the entry in dict_spec for key has one of the attributes in attrs
  before removing.

  Args:
    key: The key to remove.
    dict_spec: The dictionary to remove from.
    attrs: A list of attribute names to check for existence on
      dict_spec[key].config.
    key_exception_message: Exception message template if key is not in
      dict_spec.
    attr_exception_message: Exception message template if dict_spec[key] does
      not have a 'config' attribute or any of attrs.

  Raises:
    ClusterDirectorError: If key is not in dict_spec, or if none of attrs
      are present for dict_spec[key].config.
  """
  if key not in dict_spec:
    raise ClusterDirectorError(key_exception_message.format(id=key))
  if not getattr(dict_spec[key], "config", None):
    raise ClusterDirectorError(attr_exception_message.format(id=key))
  if not any(getattr(dict_spec[key].config, attr, None) for attr in attrs):
    raise ClusterDirectorError(attr_exception_message.format(id=key))
  dict_spec.pop(key)


def MakeClusterComputePatch(
    args: Any,
    message_module: Any,
    cluster_ref: Any,
    existing_cluster: Any,
    update_mask: MutableSet[str],
) -> Any:
  """Makes a cluster compute patch message with compute fields.

  Args:
    args: The argparse namespace.
    message_module: The API message module.
    cluster_ref: The cluster resource reference.
    existing_cluster: The existing cluster message.
    update_mask: A set of field paths to update.

  Returns:
    A message_module.Cluster.ComputeResourcesValue object with patched fields.

  Raises:
    ClusterDirectorError: If compute instances becomes empty after patch.
  """
  compute_resources = message_module.Cluster.ComputeResourcesValue()
  compute_by_id = _ConvertMessageToDict(
      existing_cluster.computeResources if existing_cluster else None
  )
  is_compute_updated = False
  if args.IsSpecified("remove_on_demand_instances"):
    for compute_id in args.remove_on_demand_instances:
      _RemoveKeyByAttrFromDictSpec(
          key=compute_id,
          dict_spec=compute_by_id,
          attrs=["newOnDemandInstances"],
          key_exception_message=_COMPUTE_INSTANCE_NOT_FOUND_ERROR,
          attr_exception_message=(
              f"On demand {_COMPUTE_INSTANCE_NOT_FOUND_ERROR}"
          ),
      )
      is_compute_updated = True
  if args.IsSpecified("remove_spot_instances"):
    for compute_id in args.remove_spot_instances:
      _RemoveKeyByAttrFromDictSpec(
          key=compute_id,
          dict_spec=compute_by_id,
          attrs=["newSpotInstances"],
          key_exception_message=_COMPUTE_INSTANCE_NOT_FOUND_ERROR,
          attr_exception_message=f"Spot {_COMPUTE_INSTANCE_NOT_FOUND_ERROR}",
      )
      is_compute_updated = True
  if args.IsSpecified("remove_reserved_instances"):
    for compute_id in args.remove_reserved_instances:
      _RemoveKeyByAttrFromDictSpec(
          key=compute_id,
          dict_spec=compute_by_id,
          attrs=["newReservedInstances"],
          key_exception_message=_COMPUTE_INSTANCE_NOT_FOUND_ERROR,
          attr_exception_message=(
              f"Reserved {_COMPUTE_INSTANCE_NOT_FOUND_ERROR}"
          ),
      )
      is_compute_updated = True
  if args.IsSpecified("remove_flex_start_instances"):
    for compute_id in args.remove_flex_start_instances:
      _RemoveKeyByAttrFromDictSpec(
          key=compute_id,
          dict_spec=compute_by_id,
          attrs=["newFlexStartInstances"],
          key_exception_message=_COMPUTE_INSTANCE_NOT_FOUND_ERROR,
          attr_exception_message=(
              f"Flex Start {_COMPUTE_INSTANCE_NOT_FOUND_ERROR}"
          ),
      )
      is_compute_updated = True
  if args.IsSpecified("add_on_demand_instances"):
    for instance in args.add_on_demand_instances:
      _AddKeyToDictSpec(
          key=instance.get("id"),
          dict_spec=compute_by_id,
          value=_MakeOnDemandComputeResource(message_module, instance),
          exception_message=_COMPUTE_INSTANCE_ALREADY_EXISTS_ERROR,
      )
      is_compute_updated = True
  if args.IsSpecified("add_spot_instances"):
    for instance in args.add_spot_instances:
      _AddKeyToDictSpec(
          key=instance.get("id"),
          dict_spec=compute_by_id,
          value=_MakeSpotComputeResource(message_module, instance),
          exception_message=_COMPUTE_INSTANCE_ALREADY_EXISTS_ERROR,
      )
      is_compute_updated = True
  if args.IsSpecified("add_reserved_instances"):
    for instance in args.add_reserved_instances:
      _AddKeyToDictSpec(
          key=instance.get("id"),
          dict_spec=compute_by_id,
          value=_MakeReservedComputeResource(
              message_module, cluster_ref, instance
          ),
          exception_message=_COMPUTE_INSTANCE_ALREADY_EXISTS_ERROR,
      )
      is_compute_updated = True
  if args.IsSpecified("add_flex_start_instances"):
    for instance in args.add_flex_start_instances:
      _AddKeyToDictSpec(
          key=instance.get("id"),
          dict_spec=compute_by_id,
          value=_MakeFlexStartComputeResource(message_module, instance),
          exception_message=_COMPUTE_INSTANCE_ALREADY_EXISTS_ERROR,
      )
      is_compute_updated = True
  if is_compute_updated:
    compute_resources.additionalProperties = [
        message_module.Cluster.ComputeResourcesValue.AdditionalProperty(
            key=key, value=value
        )
        for key, value in compute_by_id.items()
    ]
    if not compute_resources.additionalProperties:
      raise ClusterDirectorError("Compute instances cannot be empty.")
    update_mask.add("compute.resource_requests")
  return compute_resources
