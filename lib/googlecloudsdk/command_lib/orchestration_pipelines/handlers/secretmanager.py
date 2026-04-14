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
"""SecretManager resource handlers for Orchestration Pipelines."""

from typing import Any
from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base


class SecretManagerSecretHandler(base.GcpResourceHandler):
  """Handler for SecretManager Secret resources."""

  description = "SecretManager Secret resources."
  api_prefix = "projects"
  _documentation_uri = "https://cloud.google.com/secret-manager/docs/reference/rest/v1/projects.secrets"

  def _get_parent_path(self) -> str:
    """Secret Manager resources use project-level parents, not locations."""
    return f"projects/{self.environment.project}"

  def build_get_request(self) -> messages.Message:
    req_cls = self.messages.SecretmanagerProjectsSecretsGetRequest
    return req_cls(name=self._get_resource_name())

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    req_cls = self.messages.SecretmanagerProjectsSecretsCreateRequest
    return req_cls(
        parent=self._get_parent_path(),
        secretId=self.get_resource_id(),
        secret=resource_message,
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    req_cls = self.messages.SecretmanagerProjectsSecretsPatchRequest
    return req_cls(
        name=self._get_resource_name(),
        secret=resource_message,
        updateMask=",".join(changed_fields),
    )

  def get_update_method(self) -> Any:
    return self._api_client_collection.Patch
