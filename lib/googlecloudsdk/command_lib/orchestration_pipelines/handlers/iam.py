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
"""Handler for deploying IAM Service Account resources."""

from typing import Any

from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base


class IamServiceAccountHandler(base.GcpResourceHandler):
  """Handler for deploying IAM Service Accounts."""

  api_client_collection_path = "projects_serviceAccounts"

  def _get_location_path(self) -> str:
    return f"projects/{self.environment.project}"

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    project_name = f"projects/{self.environment.project}"
    account_id = self.resource.name

    create_request = self.messages.CreateServiceAccountRequest(
        accountId=account_id, serviceAccount=resource_message
    )

    return self.messages.IamProjectsServiceAccountsCreateRequest(
        name=project_name, createServiceAccountRequest=create_request
    )

  def build_get_request(self) -> Any:
    email = f"{self.resource.name}@{self.environment.project}.iam.gserviceaccount.com"
    name = f"projects/{self.environment.project}/serviceAccounts/{email}"
    return self.messages.IamProjectsServiceAccountsGetRequest(name=name)

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    patch_request = self.messages.PatchServiceAccountRequest(
        serviceAccount=resource_message, updateMask=",".join(changed_fields)
    )

    return self.messages.IamProjectsServiceAccountsPatchRequest(
        name=existing_resource.name, patchServiceAccountRequest=patch_request
    )

  def get_resource_id(self) -> str:
    return f"{self.resource.name}@{self.environment.project}.iam.gserviceaccount.com"
