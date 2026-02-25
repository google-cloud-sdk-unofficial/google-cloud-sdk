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

from apitools.base.py import encoding
from googlecloudsdk.command_lib.orchestration_pipelines import deployment_model
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base
from googlecloudsdk.core import log


class BqDataTransferConfigHandler(base.GcpResourceHandler):
  """Handler for BigQuery DataTransfer Config resources."""
  resource: deployment_model.BqDataTransferConfigModel

  api_name = "bigquerydatatransfer"
  api_version = "v1"

  def get_resource_id(self) -> str:
    return self.resource.name

  def get_create_method(self) -> Any:
    return self.client.projects_locations_transferConfigs.Create

  def get_update_method(self) -> Any:
    return self.client.projects_locations_transferConfigs.Patch

  def find_existing_resource(self) -> Any:
    parent = f"projects/{self.environment.project}/locations/{self.environment.region}"
    request = self.messages.BigquerydatatransferProjectsLocationsTransferConfigsListRequest(
        parent=parent
    )
    response = self.client.projects_locations_transferConfigs.List(request)
    matching = [
        c
        for c in response.transferConfigs
        if c.displayName == self.resource.display_name
    ]
    if len(matching) > 1:
      raise ValueError(
          f"Found {len(matching)} transfer configs with ambiguous displayName"
          f" '{self.resource.display_name}'"
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

  def get_local_definition(self) -> Dict[str, Any]:
    definition = super().get_local_definition()
    definition["displayName"] = self.resource.display_name
    return definition

  def compare(
      self, existing_resource: Any, local_definition: Dict[str, Any]
  ) -> List[str]:
    local_copy = local_definition.copy()
    local_copy.pop("service_account_name", None)
    changed = []
    for k, v in local_copy.items():
      if k == "params":
        pass  # Handled below
      elif getattr(existing_resource, k, None) != v:
        changed.append(k)
    if "params" in local_definition:
      existing_params = encoding.MessageToDict(existing_resource.params)
      if local_definition.get("params") != existing_params:
        if "params" not in changed:
          changed.append("params")
    return changed

  def build_create_request(self, definition: Dict[str, Any]) -> Any:
    parent = f"projects/{self.environment.project}/locations/{self.environment.region}"
    transfer_config_message = encoding.DictToMessage(
        definition, self.messages.TransferConfig
    )
    return self.messages.BigquerydatatransferProjectsLocationsTransferConfigsCreateRequest(
        parent=parent,
        transferConfig=transfer_config_message,
        serviceAccountName=self.resource.service_account_name,
    )

  def build_update_request(
      self,
      existing_resource: Any,
      definition: Dict[str, Any],
      changed_fields: List[str],
  ) -> Any:
    transfer_config_message = encoding.DictToMessage(
        definition, self.messages.TransferConfig
    )
    transfer_config_message.name = existing_resource.name
    mask_paths = [
        field for field in changed_fields if field != "service_account_name"
    ]
    return self.messages.BigquerydatatransferProjectsLocationsTransferConfigsPatchRequest(
        name=existing_resource.name,
        transferConfig=transfer_config_message,
        updateMask=",".join(mask_paths),
        serviceAccountName=self.resource.service_account_name,
    )
