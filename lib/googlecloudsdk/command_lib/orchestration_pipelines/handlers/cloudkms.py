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
"""CloudKMS resource handler."""

from typing import Any

from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base


class CloudKmsKeyRingHandler(base.GcpResourceHandler):
  """Handler for CloudKms KeyRing resources."""

  _documentation_uri = (
      "https://cloud.google.com/kms/docs/reference/rest/v1/"
      "projects.locations.keyRings"
  )
  description = "CloudKMS KeyRing resources."

  def build_get_request(self) -> messages.Message:
    return self.messages.CloudkmsProjectsLocationsKeyRingsGetRequest(
        name=self._get_resource_name()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.CloudkmsProjectsLocationsKeyRingsCreateRequest(
        parent=self._get_location_path(),
        keyRingId=self.get_resource_id(),
        keyRing=resource_message,
    )

  def build_delete_request(
      self, existing_resource: messages.Message
  ) -> messages.Message:
    raise NotImplementedError(
        "CloudKMS KeyRings cannot be deleted. Set updateAction: skip instead."
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    raise NotImplementedError("CloudKMS KeyRings cannot be updated.")


class CloudKmsCryptoKeyHandler(base.GcpResourceHandler):
  """Handler for CloudKms CryptoKey resources."""

  _documentation_uri = (
      "https://cloud.google.com/kms/docs/reference/rest/v1/"
      "projects.locations.keyRings.cryptoKeys"
  )
  description = "CloudKMS CryptoKey resources."

  def build_get_request(self) -> messages.Message:
    return self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
        name=self._get_resource_name()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    parent = self._get_parent_path()

    req_cls = (
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest
    )
    return req_cls(
        parent=parent,
        cryptoKeyId=self.get_resource_id(),
        cryptoKey=resource_message,
    )

  def build_delete_request(
      self, existing_resource: messages.Message
  ) -> messages.Message:
    raise NotImplementedError(
        "CloudKMS CryptoKeys cannot be deleted. Set updateAction: skip instead."
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    req_cls = (
        self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest
    )
    return req_cls(
        name=self._get_resource_name(),
        cryptoKey=resource_message,
        updateMask=",".join(changed_fields),
    )

  def get_update_method(self) -> Any:
    return self._api_client_collection.Patch
