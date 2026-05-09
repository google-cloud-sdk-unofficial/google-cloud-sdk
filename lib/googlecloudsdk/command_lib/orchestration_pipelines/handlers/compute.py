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
"""Compute resource handler."""

import copy
from typing import Any

from apitools.base.protorpclite import messages
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base
from googlecloudsdk.core import exceptions


class ComputeNetworkHandler(base.GcpResourceHandler):
  """Handler for Compute Network resources."""

  description = "Compute Network resources."
  api_prefix = ""

  def build_get_request(self) -> messages.Message:
    return self.messages.ComputeNetworksGetRequest(
        project=self.environment.project, network=self.get_resource_id()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.ComputeNetworksInsertRequest(
        project=self.environment.project,
        network=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    return self.messages.ComputeNetworksPatchRequest(
        project=self.environment.project,
        network=self.get_resource_id(),
        networkResource=resource_message,
    )

  def get_update_method(self) -> Any:
    return self._api_client_collection.Patch


class ComputeSubnetworkHandler(base.GcpResourceHandler):
  """Handler for Compute Subnetwork resources."""

  description = (
      "Compute Subnetwork resources.\n"
      "Special handling:\n"
      " - network: ignored during update API calls"
  )
  api_prefix = ""

  def build_get_request(self) -> messages.Message:
    return self.messages.ComputeSubnetworksGetRequest(
        project=self.environment.project,
        region=self.location,
        subnetwork=self.get_resource_id(),
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.ComputeSubnetworksInsertRequest(
        project=self.environment.project,
        region=self.location,
        subnetwork=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    if (
        hasattr(existing_resource, "fingerprint")
        and existing_resource.fingerprint
    ):
      resource_message.fingerprint = existing_resource.fingerprint

    # Subnetwork API doesn't allow patching the network field
    resource_message.network = None

    return self.messages.ComputeSubnetworksPatchRequest(
        project=self.environment.project,
        region=self.location,
        subnetwork=self.get_resource_id(),
        subnetworkResource=resource_message,
    )

  def get_update_method(self) -> Any:
    return self._api_client_collection.Patch


class ComputeFirewallHandler(base.GcpResourceHandler):
  """Handler for Compute Firewall resources."""

  description = "Compute Firewall resources."
  api_prefix = ""

  def build_get_request(self) -> messages.Message:
    return self.messages.ComputeFirewallsGetRequest(
        project=self.environment.project, firewall=self.get_resource_id()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.ComputeFirewallsInsertRequest(
        project=self.environment.project,
        firewall=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    return self.messages.ComputeFirewallsPatchRequest(
        project=self.environment.project,
        firewall=self.get_resource_id(),
        firewallResource=resource_message,
    )

  def get_update_method(self) -> Any:
    return self._api_client_collection.Patch


class ComputeRouterHandler(base.GcpResourceHandler):
  """Handler for Compute Router resources."""

  description = "Compute Router resources."
  api_prefix = ""

  def build_get_request(self) -> messages.Message:
    return self.messages.ComputeRoutersGetRequest(
        project=self.environment.project,
        region=self.location,
        router=self.get_resource_id(),
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.ComputeRoutersInsertRequest(
        project=self.environment.project,
        region=self.location,
        router=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    return self.messages.ComputeRoutersPatchRequest(
        project=self.environment.project,
        region=self.location,
        router=self.get_resource_id(),
        routerResource=resource_message,
    )

  def get_update_method(self) -> Any:
    return self._api_client_collection.Patch


class ComputeRouterNatHandler(base.GcpResourceHandler):
  """Handler for Compute Router NAT resources.

  Note: NATs are updated via patch to the Router.
  """

  description = (
      "Compute Router NAT resources.\n"
      "Special handling:\n"
      " - lifecycle: created and updated by patching the parent Router"
  )
  api_prefix = ""

  def build_get_request(self) -> messages.Message:
    # Router NATs are typically managed as part of the Router resource.
    # We fetch the router that contains it.
    req_cls = self.messages.ComputeRoutersGetRequest
    return req_cls(
        project=self.environment.project,
        region=self.location,
        router=self.resource.definition.get("router", ""),
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    raise NotImplementedError(
        "Router NATs should be created by patching the parent Router."
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    raise NotImplementedError(
        "Router NATs should be updated by patching the parent Router."
    )


class ComputeForwardingRuleHandler(base.GcpResourceHandler):
  """Handler for Compute Forwarding Rule resources."""

  description = (
      "Compute Forwarding Rule resources.\n"
      "Special handling:\n"
      " - portRange: automatically normalized during comparison (e.g., '80' "
      "becomes '80-80')"
  )
  api_prefix = ""

  def compare(
      self,
      existing_resource: messages.Message,
      local_definition: dict[str, Any],
  ) -> list[str]:
    """Overrides compare to handle server-side portRange normalization."""
    # Compute API converts '80' to '80-80' automatically.
    # To prevent false positives, we coerce the local definition to match the
    # server's format prior to comparison if it's a single port string.
    port_range = local_definition.get("portRange")
    if port_range is not None and "-" not in str(port_range):
      local_definition["portRange"] = f"{port_range}-{port_range}"

    return super().compare(existing_resource, local_definition)

  def build_get_request(self) -> messages.Message:
    return self.messages.ComputeForwardingRulesGetRequest(
        project=self.environment.project,
        region=self.location,
        forwardingRule=self.get_resource_id(),
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.ComputeForwardingRulesInsertRequest(
        project=self.environment.project,
        region=self.location,
        forwardingRule=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> dict[str, Any]:
    requests = {}

    if "labels" in changed_fields:
      labels_properties = []
      if resource_message.labels and hasattr(
          resource_message.labels, "additionalProperties"
      ):
        for prop in resource_message.labels.additionalProperties:
          labels_properties.append(
              self.messages.RegionSetLabelsRequest.LabelsValue.AdditionalProperty(
                  key=prop.key, value=prop.value
              )
          )

      requests["set_labels"] = (
          self.messages.ComputeForwardingRulesSetLabelsRequest(
              project=self.environment.project,
              region=self.location,
              resource=self.get_resource_id(),
              regionSetLabelsRequest=self.messages.RegionSetLabelsRequest(
                  labelFingerprint=existing_resource.labelFingerprint,
                  labels=self.messages.RegionSetLabelsRequest.LabelsValue(
                      additionalProperties=labels_properties
                  ),
              ),
          )
      )

    if "target" in changed_fields:
      requests["set_target"] = (
          self.messages.ComputeForwardingRulesSetTargetRequest(
              project=self.environment.project,
              forwardingRule=self.get_resource_id(),
              region=self.location,
              targetReference=self.messages.TargetReference(
                  target=resource_message.target
              ),
          )
      )

    # Filter out labels and target from changed_fields for Patch
    other_fields = [f for f in changed_fields if f not in ["labels", "target"]]

    if other_fields:
      update_resource = self.messages.ForwardingRule()
      for field in other_fields:
        if hasattr(resource_message, field):
          setattr(update_resource, field, getattr(resource_message, field))

      requests["patch"] = self.messages.ComputeForwardingRulesPatchRequest(
          project=self.environment.project,
          region=self.location,
          forwardingRule=self.get_resource_id(),
          forwardingRuleResource=update_resource,
      )

    return requests

  def get_update_method(self) -> Any:

    def _update(request: dict[str, Any]):
      response = None

      if "set_labels" in request:
        response = self._api_client_collection.SetLabels(request["set_labels"])

      if "set_target" in request:
        if response:
          self.wait_for_operation(response)
        response = self._api_client_collection.SetTarget(request["set_target"])

      if "patch" in request:
        if response:
          self.wait_for_operation(response)
        response = self._api_client_collection.Patch(request["patch"])

      return response

    return _update


class ComputeAddressHandler(base.GcpResourceHandler):
  """Handler for Compute Address resources."""

  description = (
      "Compute Address resources.\n"
      "Special handling:\n"
      " - updates: in-place updates are supported only for labels"
  )
  api_prefix = ""
  api_client_collection_path = "addresses"

  def get_local_definition(self) -> dict[str, Any]:
    definition = super().get_local_definition()
    if definition.get("name") and definition["name"] != self.resource.name:
      raise ValueError(
          f"The name inside the definition block ('{definition['name']}') "
          "cannot be different from the logical name of the resource "
          f"('{self.resource.name}'). Please remove it from the definition."
      )
    definition["name"] = self.resource.name
    return definition

  def get_labels_field_name(self) -> str | None:
    """Disable base handler's label detection to handle it manually."""
    return None

  def to_resource_message(self, definition: dict[str, Any]) -> messages.Message:
    """Converts a dictionary definition to a resource message."""
    definition_copy = copy.deepcopy(definition)
    labels_dict = definition_copy.pop("labels", {})
    labels_dict[base.IMPLICIT_LABEL_KEY] = base.IMPLICIT_LABEL_VALUE

    resource_msg = super().to_resource_message(definition_copy)

    resource_msg.labels = self._build_labels_value(
        self.messages.Address.LabelsValue, labels_dict
    )

    return resource_msg

  def build_get_request(self) -> messages.Message:
    return self.messages.ComputeAddressesGetRequest(
        project=self.environment.project,
        region=self.environment.region,
        address=self.get_resource_id(),
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.ComputeAddressesInsertRequest(
        project=self.environment.project,
        region=self.environment.region,
        address=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def should_retry_create(self, exception: Exception) -> bool:
    if isinstance(exception, apitools_exceptions.HttpError):
      return exception.response.status == 409
    return False

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> dict[str, Any]:
    unsupported_fields = [f for f in changed_fields if f != "labels"]
    if unsupported_fields:
      raise NotImplementedError(
          "ComputeAddressHandler does not support updating fields:"
          f" {unsupported_fields}. Only 'labels' can be updated in-place."
      )

    requests = {}

    if "labels" in changed_fields:
      labels_properties = []
      if resource_message.labels and hasattr(
          resource_message.labels, "additionalProperties"
      ):
        for prop in resource_message.labels.additionalProperties:
          labels_properties.append(
              self.messages.RegionSetLabelsRequest.LabelsValue.AdditionalProperty(
                  key=prop.key, value=prop.value
              )
          )

      requests["set_labels"] = self.messages.ComputeAddressesSetLabelsRequest(
          project=self.environment.project,
          region=self.environment.region,
          resource=self.get_resource_id(),
          regionSetLabelsRequest=self.messages.RegionSetLabelsRequest(
              labelFingerprint=existing_resource.labelFingerprint,
              labels=self.messages.RegionSetLabelsRequest.LabelsValue(
                  additionalProperties=labels_properties
              ),
          ),
      )

    return requests

  def get_update_method(self) -> Any:
    def _update(request):
      response = None
      if "set_labels" in request:
        response = self._api_client_collection.SetLabels(request["set_labels"])
      return response

    return _update

  def build_delete_request(
      self, existing_resource: messages.Message
  ) -> messages.Message:
    del existing_resource  # Unused
    return self.messages.ComputeAddressesDeleteRequest(
        project=self.environment.project,
        region=self.environment.region,
        address=self.get_resource_id(),
    )


class ComputeInstanceHandler(base.GcpResourceHandler):
  """Handler for Compute Instance resources."""

  description = (
      "Compute Instance resources.\n"
      "Special handling:\n"
      " - zone: derived from metadata.location if omitted\n"
      " - disks[].initializeParams: ignored during comparison"
  )
  api_prefix = ""

  @property
  def zone(self) -> str:
    zone = self.resource.definition.get("zone")
    if not zone:
      zone = self.resource.metadata.location
      if not zone:
        raise exceptions.Error(
            f"Failed to deploy resource '{self.resource.name}' of type "
            f"'{self.resource.type}': Missing target zone. Must be specified "
            "in definition['zone'] or metadata['location']."
        )
    return zone

  def get_local_definition(self) -> dict[str, Any]:
    definition = super().get_local_definition()
    if definition.get("name") and definition["name"] != self.resource.name:
      raise ValueError(
          f"The name inside the definition block ('{definition['name']}') "
          "cannot be different from the logical name of the resource "
          f"('{self.resource.name}'). Please remove it from the definition."
      )
    definition["name"] = self.resource.name
    definition["zone"] = self.zone
    return definition

  def get_labels_field_name(self) -> str | None:
    """Disable base handler's label detection to handle it manually."""
    return None

  def to_resource_message(self, definition: dict[str, Any]) -> messages.Message:
    """Converts a dictionary definition to a resource message."""
    definition_copy = copy.deepcopy(definition)
    labels_dict = definition_copy.pop("labels", {}) or {}
    labels_dict[base.IMPLICIT_LABEL_KEY] = base.IMPLICIT_LABEL_VALUE

    resource_msg = super().to_resource_message(definition_copy)

    resource_msg.labels = self._build_labels_value(
        self.messages.Instance.LabelsValue, labels_dict
    )

    return resource_msg

  def compare(
      self, existing_resource: Any, local_definition: dict[str, Any]
  ) -> list[str]:
    """Drops one-time creation fields off disks prior to evaluating."""
    if "disks" in local_definition:
      for disk in local_definition["disks"]:
        if "initializeParams" in disk:
          disk.pop("initializeParams")

    return super().compare(existing_resource, local_definition)

  def build_get_request(self) -> messages.Message:
    req_cls = self.messages.ComputeInstancesGetRequest
    return req_cls(
        project=self.environment.project,
        zone=self.zone,
        instance=self.get_resource_id(),
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    req_cls = self.messages.ComputeInstancesInsertRequest
    return req_cls(
        project=self.environment.project,
        zone=self.zone,
        instance=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:

    if (
        hasattr(existing_resource, "fingerprint")
        and existing_resource.fingerprint
    ):
      resource_message.fingerprint = existing_resource.fingerprint

    req_cls = self.messages.ComputeInstancesUpdateRequest
    return req_cls(
        project=self.environment.project,
        zone=self.zone,
        instance=self.get_resource_id(),
        instanceResource=resource_message,
    )

  def get_update_method(self) -> Any:
    return self._api_client_collection.Update


class ComputeInstanceTemplateHandler(base.GcpResourceHandler):
  """Handler for Compute Instance Template resources."""

  description = (
      "Compute Instance Template resources.\n"
      "Special handling:\n"
      " - updates: in-place updates are not supported"
  )
  api_prefix = ""

  def build_get_request(self) -> messages.Message:
    return self.messages.ComputeInstanceTemplatesGetRequest(
        project=self.environment.project,
        instanceTemplate=self.get_resource_id(),
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.ComputeInstanceTemplatesInsertRequest(
        project=self.environment.project,
        instanceTemplate=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    raise NotImplementedError(
        "Compute Instance Templates cannot be updated in-place."
    )

  def build_delete_request(
      self, existing_resource: messages.Message
  ) -> messages.Message:
    del existing_resource  # Unused
    return self.messages.ComputeInstanceTemplatesDeleteRequest(
        project=self.environment.project,
        instanceTemplate=self.get_resource_id(),
    )


class ComputeInstanceGroupManagerHandler(base.GcpResourceHandler):
  """Handler for Compute Instance Group Manager resources."""

  description = (
      "Compute Instance Group Manager resources.\n"
      "Special handling:\n"
      " - zone: derived from metadata.location if omitted"
  )
  api_prefix = ""

  @property
  def zone(self) -> str:
    zone = self.resource.definition.get("zone")
    if not zone:
      zone = self.resource.metadata.location
      if not zone:
        raise exceptions.Error(
            f"Failed to deploy resource '{self.resource.name}' of type "
            f"'{self.resource.type}': Missing target zone. Must be specified "
            "in definition['zone'] or metadata['location']."
        )
    return zone

  def get_local_definition(self) -> dict[str, Any]:
    definition = super().get_local_definition()
    if definition.get("name") and definition["name"] != self.resource.name:
      raise ValueError(
          f"The name inside the definition block ('{definition['name']}') "
          "cannot be different from the logical name of the resource "
          f"('{self.resource.name}'). Please remove it from the definition."
      )
    definition["name"] = self.resource.name
    definition["zone"] = self.zone
    return definition

  def build_get_request(self) -> messages.Message:
    req_cls = self.messages.ComputeInstanceGroupManagersGetRequest
    return req_cls(
        project=self.environment.project,
        zone=self.zone,
        instanceGroupManager=self.get_resource_id(),
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    req_cls = self.messages.ComputeInstanceGroupManagersInsertRequest
    return req_cls(
        project=self.environment.project,
        zone=self.zone,
        instanceGroupManager=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    req_cls = self.messages.ComputeInstanceGroupManagersPatchRequest
    return req_cls(
        project=self.environment.project,
        zone=self.zone,
        instanceGroupManager=self.get_resource_id(),
        instanceGroupManagerResource=resource_message,
    )

  def get_update_method(self) -> Any:
    return self._api_client_collection.Patch


class ComputeRouteHandler(base.GcpResourceHandler):
  """Handler for Compute Route resources."""

  description = (
      "Compute Route resources.\n"
      "Special handling:\n"
      " - updates: in-place updates are not supported"
  )
  api_prefix = ""

  def build_get_request(self) -> messages.Message:
    return self.messages.ComputeRoutesGetRequest(
        project=self.environment.project, route=self.get_resource_id()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.ComputeRoutesInsertRequest(
        project=self.environment.project,
        route=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    # Cannot patch routes
    raise NotImplementedError("Compute Routes update not fully supported.")

  def build_delete_request(
      self, existing_resource: messages.Message
  ) -> messages.Message:
    del existing_resource  # Unused
    return self.messages.ComputeRoutesDeleteRequest(
        project=self.environment.project,
        route=self.get_resource_id(),
    )


class ComputeNetworkPeeringHandler(base.GcpResourceHandler):
  """Handler for Compute Network Peering resources.

  Note: Peerings are managed via network patch/methods.
  """

  description = (
      "Compute Network Peering resources.\n"
      "Special handling:\n"
      " - lifecycle: managed via parent Network peering methods (AddPeering, "
      "UpdatePeering)"
  )
  api_prefix = ""
  api_client_collection_path = "networks"

  def build_get_request(self) -> messages.Message:
    return self.messages.ComputeNetworksGetRequest(
        project=self.environment.project,
        network=self.get_validated_parent_id(),
    )

  def find_existing_resource(self) -> Any:
    """Finds the existing peering resource from the network."""
    request = self.build_get_request()
    network = self.get_get_method()(request)
    if network and network.peerings:
      for peering in network.peerings:
        if peering.name == self.get_resource_id():
          return peering
    return None

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    req_msg = self.messages.NetworksAddPeeringRequest(
        name=self.get_resource_id(),
        networkPeering=resource_message,
    )
    return self.messages.ComputeNetworksAddPeeringRequest(
        project=self.environment.project,
        network=self.get_validated_parent_id(),
        networksAddPeeringRequest=req_msg,
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    resource_message.name = self.get_resource_id()
    req_msg = self.messages.NetworksUpdatePeeringRequest(
        networkPeering=resource_message,
    )
    return self.messages.ComputeNetworksUpdatePeeringRequest(
        project=self.environment.project,
        network=self.get_validated_parent_id(),
        networksUpdatePeeringRequest=req_msg,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.AddPeering

  def get_update_method(self) -> Any:
    return self._api_client_collection.UpdatePeering


class ComputeTargetInstanceHandler(base.GcpResourceHandler):
  """Handler for Compute Target Instance resources."""

  description = (
      "Compute Target Instance resources.\n"
      "Special handling:\n"
      " - updates: in-place updates are not supported"
  )
  api_prefix = ""
  api_client_collection_path = "targetInstances"

  def build_get_request(self) -> messages.Message:
    return self.messages.ComputeTargetInstancesGetRequest(
        project=self.environment.project,
        zone=self.location,
        targetInstance=self.get_resource_id(),
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.ComputeTargetInstancesInsertRequest(
        project=self.environment.project,
        zone=self.location,
        targetInstance=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    raise NotImplementedError("Update is not supported for target instances.")

  def get_update_method(self) -> Any:
    return getattr(self._api_client_collection, "Patch", None)

  def build_delete_request(
      self, existing_resource: messages.Message
  ) -> messages.Message:
    del existing_resource  # Unused
    return self.messages.ComputeTargetInstancesDeleteRequest(
        project=self.environment.project,
        zone=self.location,
        targetInstance=self.get_resource_id(),
    )
