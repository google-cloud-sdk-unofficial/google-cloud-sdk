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
"""Artifact Registry resource handler."""

from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base


class ArtifactRegistryRepositoryHandler(base.GcpResourceHandler):
  """Handler for ArtifactRegistry Repository resources."""

  description = "Artifact Registry repository configurations."

  def get_documentation_uri(self) -> str:
    return "https://cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories"

  def build_get_request(self) -> messages.Message:
    req_cls = (
        self.messages.ArtifactregistryProjectsLocationsRepositoriesGetRequest
    )
    return req_cls(name=self._get_resource_name())

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    req_cls = (
        self.messages.ArtifactregistryProjectsLocationsRepositoriesCreateRequest
    )
    return req_cls(
        parent=self._get_parent_path(),
        repositoryId=self.get_resource_id(),
        repository=resource_message,
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    req_cls = (
        self.messages.ArtifactregistryProjectsLocationsRepositoriesPatchRequest
    )
    return req_cls(
        name=self._get_resource_name(),
        repository=resource_message,
        updateMask=",".join(changed_fields),
    )
