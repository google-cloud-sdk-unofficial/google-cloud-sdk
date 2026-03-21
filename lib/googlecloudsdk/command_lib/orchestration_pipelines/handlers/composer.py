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
"""Composer Environment resource handler."""

from typing import List

from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base


class ComposerEnvironmentHandler(base.GcpResourceHandler):
  """Handler for migrating Composer Environment configurations."""

  api_client_collection_path = "projects_locations_environments"

  def build_get_request(self) -> messages.Message:
    return self.messages.ComposerProjectsLocationsEnvironmentsGetRequest(
        name=self._get_resource_name()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    resource_message.name = self._get_resource_name()
    return self.messages.ComposerProjectsLocationsEnvironmentsCreateRequest(
        parent=self._get_location_path(),
        environment=resource_message,
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: List[str],
  ) -> messages.Message:
    resource_message.name = existing_resource.name
    return self.messages.ComposerProjectsLocationsEnvironmentsPatchRequest(
        name=existing_resource.name,
        environment=resource_message,
        updateMask=",".join(changed_fields),
    )
