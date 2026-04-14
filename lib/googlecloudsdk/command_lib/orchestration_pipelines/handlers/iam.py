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
  api_prefix = "projects"
  description = (
      "IAM Service Accounts.\n"
      "Special handling:\n"
      " - resource ID: implicitly formatted as email address "
      "({name}@{project}.iam.gserviceaccount.com) for API requests"
  )

  def _get_location_path(self) -> str:
    return f"projects/{self.environment.project}"

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    account_id = self.resource.name

    create_request = self.messages.CreateServiceAccountRequest(
        accountId=account_id, serviceAccount=resource_message
    )

    return self.messages.IamProjectsServiceAccountsCreateRequest(
        name=self._get_location_path(),
        createServiceAccountRequest=create_request,
    )

  def build_get_request(self) -> Any:
    return self.messages.IamProjectsServiceAccountsGetRequest(
        name=self._get_resource_name()
    )

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


class IamServiceAccountIamPolicyHandler(base.GcpResourceHandler):
  """Handler for deploying IAM Service Account policies."""

  description = "IAM Service Account policies."
  api_client_collection_path = "projects_serviceAccounts"
  collection_name = "serviceAccounts"

  @property
  def resource_message_type(self) -> type[messages.Message]:
    return self.messages.Policy

  def _get_location_path(self) -> str:
    return f"projects/{self.environment.project}"

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    # Requires special client handling since SetIamPolicy returns a Policy

    return self.messages.IamProjectsServiceAccountsSetIamPolicyRequest(
        resource=self._get_resource_name(),
        setIamPolicyRequest=self.messages.SetIamPolicyRequest(
            policy=resource_message
        ),
    )

  def build_get_request(self) -> Any:
    return self.messages.IamProjectsServiceAccountsGetIamPolicyRequest(
        resource=self._get_resource_name()
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:

    return self.messages.IamProjectsServiceAccountsSetIamPolicyRequest(
        resource=self._get_resource_name(),
        setIamPolicyRequest=self.messages.SetIamPolicyRequest(
            policy=resource_message
        ),
    )

  def get_get_method(self) -> Any:
    return self._api_client_collection.GetIamPolicy

  def get_create_method(self) -> Any:
    return self._api_client_collection.SetIamPolicy

  def get_update_method(self) -> Any:
    return self._api_client_collection.SetIamPolicy

  def get_resource_id(self) -> str:
    return f"{self.resource.name}@{self.environment.project}.iam.gserviceaccount.com"


class IamWorkloadIdentityPoolHandler(base.GcpResourceHandler):
  """Handler for deploying IAM Workload Identity Pools."""

  description = "IAM Workload Identity Pools."

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.IamProjectsLocationsWorkloadIdentityPoolsCreateRequest(
        parent=self._get_parent_path(),
        workloadIdentityPoolId=self.resource.name,
        workloadIdentityPool=resource_message,
    )

  def build_get_request(self) -> Any:
    return self.messages.IamProjectsLocationsWorkloadIdentityPoolsGetRequest(
        name=self._get_resource_name()
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    return self.messages.IamProjectsLocationsWorkloadIdentityPoolsPatchRequest(
        name=existing_resource.name,
        workloadIdentityPool=resource_message,
        updateMask=",".join(changed_fields),
    )


class IamWorkloadIdentityPoolProviderHandler(base.GcpResourceHandler):
  """Handler for deploying IAM Workload Identity Pool Providers."""

  description = "IAM Workload Identity Pool Providers."
  collection_name = "providers"
  _documentation_uri = "https://cloud.google.com/iam/docs/reference/rest/v1/projects.locations.workloadIdentityPools.providers"

  def _get_parent_path(self) -> str:
    return f"{self._get_location_path()}/workloadIdentityPools/{self.get_validated_parent_id()}"

  @property
  def _api_client_collection(self) -> Any:
    return self.client.projects_locations_workloadIdentityPools_providers

  def get_create_method(self) -> Any:
    return self._api_client_collection.Create

  def get_update_method(self) -> Any:
    return self._api_client_collection.Patch

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.IamProjectsLocationsWorkloadIdentityPoolsProvidersCreateRequest(
        parent=self._get_parent_path(),
        workloadIdentityPoolProviderId=self.resource.name,
        workloadIdentityPoolProvider=resource_message,
    )

  def build_get_request(self) -> Any:
    return self.messages.IamProjectsLocationsWorkloadIdentityPoolsProvidersGetRequest(
        name=self._get_resource_name()
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    resource_message.name = existing_resource.name
    return self.messages.IamProjectsLocationsWorkloadIdentityPoolsProvidersPatchRequest(
        name=existing_resource.name,
        workloadIdentityPoolProvider=resource_message,
        updateMask=",".join(changed_fields),
    )
