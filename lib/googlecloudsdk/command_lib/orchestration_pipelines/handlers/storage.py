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
"""Storage resource handlers."""

from typing import Any
from apitools.base.protorpclite import messages
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base


class StorageBucketHandler(base.GcpResourceHandler):
  """Handler for Storage Bucket resources."""

  description = "Storage Bucket resources."
  api_prefix = ""

  def build_get_request(self) -> messages.Message:
    return self.messages.StorageBucketsGetRequest(bucket=self.get_resource_id())

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    resource_message.name = self.get_resource_id()
    return self.messages.StorageBucketsInsertRequest(
        project=self.environment.project,
        bucket=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    # Storage API uses Patch
    return self.messages.StorageBucketsPatchRequest(
        bucket=self.get_resource_id(),
        bucketResource=resource_message,
    )

  def get_update_method(self) -> Any:
    return self._api_client_collection.Patch


class StorageNotificationHandler(base.GcpResourceHandler):
  """Handler for Storage Notification resources."""

  description = (
      "Storage Notification resources.\n"
      "Special handling:\n"
      " - updates: in-place updates are not supported by the API; resources "
      "must be recreated\n"
      " - dynamic ID resolution: resource ID is resolved dynamically from "
      "matching topic in API list output\n"
      "Definition handling:\n"
      " - topic: prefix `//pubsub.[DOMAIN]/` is ignored during "
      "comparison against API state"
  )
  api_prefix = ""
  api_client_collection_path = "notifications"

  def build_get_request(self) -> messages.Message:
    req = self.messages.StorageNotificationsListRequest(
        bucket=self.get_validated_parent_id(),
    )
    return req

  def get_get_method(self) -> Any:
    return self._api_client_collection.List

  def compare(
      self,
      existing_resource: Any,
      local_definition: dict[str, Any],
  ) -> list[str]:
    # API returns topics like '//pubsub.[DOMAIN]/projects/X/topics/Y'
    if hasattr(existing_resource, "topic") and existing_resource.topic:
      if "projects/" in existing_resource.topic:
        # Extract just the projects/... part
        existing_resource.topic = (
            "projects/" + existing_resource.topic.split("projects/", 1)[1]
        )

    return super().compare(existing_resource, local_definition)

  def find_existing_resource(self) -> Any:
    request = self.build_get_request()
    try:
      response = self.get_get_method()(request)
    except apitools_exceptions.HttpNotFoundError:
      return None

    local_topic = self.get_local_definition().get("topic")
    if not local_topic:
      return None

    for notification in getattr(response, "items", []):
      # API returns topics like '//pubsub.[DOMAIN]/projects/X/topics/Y'
      if notification.topic and notification.topic.endswith(local_topic):
        self._dynamically_resolved_id = notification.id
        return notification

    return None

  def get_resource_id(self) -> str:
    if hasattr(self, "_dynamically_resolved_id"):
      if getattr(self, "_dynamically_resolved_id"):
        return self._dynamically_resolved_id
    return super().get_resource_id()

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.StorageNotificationsInsertRequest(
        bucket=self.get_validated_parent_id(),
        notification=resource_message,
    )

  def get_create_method(self) -> Any:
    return self._api_client_collection.Insert

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    # Storage Notifications cannot be patched/updated.
    # Therefore, we raise an error.
    raise NotImplementedError(
        "Storage Notifications cannot be updated, only recreated."
    )


class StorageBucketIamPolicyHandler(base.GcpResourceHandler):
  """Handler for Storage Bucket IAM Policy resources."""

  description = "Storage Bucket IAM Policy resources."
  api_prefix = ""
  api_client_collection_path = "buckets"

  @property
  def resource_message_type(self) -> type[messages.Message]:
    return self.messages.Policy

  def build_get_request(self) -> messages.Message:
    return self.messages.StorageBucketsGetIamPolicyRequest(
        bucket=self.get_validated_parent_id()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.StorageBucketsSetIamPolicyRequest(
        bucket=self.get_validated_parent_id(),
        policy=resource_message,
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    return self.messages.StorageBucketsSetIamPolicyRequest(
        bucket=self.get_validated_parent_id(),
        policy=resource_message,
    )

  def get_update_method(self):
    return self._api_client_collection.SetIamPolicy

  def get_create_method(self):
    return self._api_client_collection.SetIamPolicy

  def get_get_method(self) -> Any:
    return self._api_client_collection.GetIamPolicy
