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
"""PubSub resource handler."""

from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base


class PubsubBaseHandler(base.GcpResourceHandler):
  """Base Handler for Pubsub resources."""

  api_prefix = "projects"

  def _get_parent_path(self) -> str:
    location_path = f"projects/{self.environment.project}"
    if self.resource.parent:
      return f"{location_path}{self.resource.parent}"
    return location_path


class PubsubTopicHandler(PubsubBaseHandler):
  """Handler for Pubsub Topic resources."""

  description = "Pubsub Topic resources."

  def build_get_request(self) -> messages.Message:
    return self.messages.PubsubProjectsTopicsGetRequest(
        topic=self._get_resource_name()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    resource_message.name = self._get_resource_name()
    return resource_message

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    resource_message.name = existing_resource.name
    return self.messages.PubsubProjectsTopicsPatchRequest(
        name=existing_resource.name,
        updateTopicRequest=self.messages.UpdateTopicRequest(
            topic=resource_message,
            updateMask=",".join(changed_fields),
        ),
    )

  def get_update_method(self):
    return self._api_client_collection.Patch


class PubsubSubscriptionHandler(PubsubBaseHandler):
  """Handler for Pubsub Subscription resources."""

  description = "Pubsub Subscription resources."

  def build_get_request(self) -> messages.Message:
    return self.messages.PubsubProjectsSubscriptionsGetRequest(
        subscription=self._get_resource_name()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    resource_message.name = self._get_resource_name()
    return resource_message

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    resource_message.name = existing_resource.name
    return self.messages.PubsubProjectsSubscriptionsPatchRequest(
        name=existing_resource.name,
        updateSubscriptionRequest=self.messages.UpdateSubscriptionRequest(
            subscription=resource_message,
            updateMask=",".join(changed_fields),
        ),
    )

  def get_update_method(self):
    return self._api_client_collection.Patch


class PubsubSchemaHandler(PubsubBaseHandler):
  """Handler for Pubsub Schema resources."""

  description = (
      "Pubsub Schema resources.\n"
      "Special handling:\n"
      " - updates: in-place updates are not fully supported yet"
  )

  def build_get_request(self) -> messages.Message:
    return self.messages.PubsubProjectsSchemasGetRequest(
        name=self._get_resource_name()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.PubsubProjectsSchemasCreateRequest(
        parent=self._get_parent_path(),
        schema=resource_message,
        schemaId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    # Schemas rarely updatable in-place, but some APIs support patch.
    raise NotImplementedError(
        "PubSub Schema update is not fully supported yet."
    )

  def build_delete_request(
      self, existing_resource: messages.Message
  ) -> messages.Message:
    return self.messages.PubsubProjectsSchemasDeleteRequest(
        name=self._get_resource_name()
    )
