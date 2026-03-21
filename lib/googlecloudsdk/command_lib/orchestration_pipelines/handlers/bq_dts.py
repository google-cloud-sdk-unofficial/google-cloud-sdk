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
"""BigQuery DTS resource handler."""

from typing import Any, Dict, List

from apitools.base.protorpclite import messages
from apitools.base.py import encoding
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base
from googlecloudsdk.core import log


class BqDataTransferConfigHandler(base.GcpResourceHandler):
  """Handler for migrating BigQuery DTS configurations."""

  def find_existing_resource(self) -> Any:
    request = self.messages.BigquerydatatransferProjectsLocationsTransferConfigsListRequest(
        parent=self._get_location_path()
    )
    response = self.client.projects_locations_transferConfigs.List(request)
    expected_display_name = self.resource.definition.get(
        "displayName", self.resource.name
    )
    matching = [
        c
        for c in response.transferConfigs
        if c.displayName == expected_display_name
    ]
    if len(matching) > 1:
      raise ValueError(
          f"Found {len(matching)} transfer configs with ambiguous displayName"
          f" '{self.resource.name}'"
      )
    if matching:
      full_config_name = matching[0].name
      if self.debug:
        log.status.Print(
            f"  - Found matching config: {full_config_name}. Fetching full"
            " details."
        )
      get_request = self.messages.BigquerydatatransferProjectsLocationsTransferConfigsGetRequest(
          name=full_config_name
      )
      return self.client.projects_locations_transferConfigs.Get(get_request)
    return None

  def build_get_request(self) -> Any:
    raise NotImplementedError(
        "BqDataTransferConfigHandler overrides find_existing_resource."
    )

  def get_local_definition(self) -> Dict[str, Any]:
    definition = super().get_local_definition()
    if "displayName" not in definition:
      definition["displayName"] = self.resource.name
    return definition

  def compare(
      self, existing_resource: Any, local_definition: Dict[str, Any]
  ) -> List[str]:
    changes = []

    # Check definition fields
    for k, v in local_definition.items():
      if k == "params":
        continue  # Handled below
      if getattr(existing_resource, k, None) != v:
        changes.append(k)

    # Check params
    if "params" in local_definition:
      existing_params = encoding.MessageToDict(existing_resource.params)
      if local_definition.get("params") != existing_params:
        if "params" not in changes:
          changes.append("params")

    return changes

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    service_account_name = None
    if self.resource.metadata:
      service_account_name = self.resource.metadata.service_account_name
    return self.messages.BigquerydatatransferProjectsLocationsTransferConfigsCreateRequest(
        parent=self._get_location_path(),
        transferConfig=resource_message,
        serviceAccountName=service_account_name,
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: List[str],
  ) -> messages.Message:
    service_account_name = None
    if self.resource.metadata:
      service_account_name = self.resource.metadata.service_account_name
    resource_message.name = existing_resource.name
    return self.messages.BigquerydatatransferProjectsLocationsTransferConfigsPatchRequest(
        name=existing_resource.name,
        transferConfig=resource_message,
        updateMask=",".join(changed_fields),
        serviceAccountName=service_account_name,
    )
