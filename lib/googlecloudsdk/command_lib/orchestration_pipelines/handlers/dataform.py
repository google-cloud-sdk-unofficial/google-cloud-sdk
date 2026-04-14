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
"""Dataform resource handler."""

from typing import Any, Dict

from apitools.base.protorpclite import messages
from apitools.base.py import encoding
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import base
from googlecloudsdk.core import log


class DataformRepositoryHandler(base.GcpResourceHandler):
  """Handler for Dataform Repository resources."""

  _documentation_uri = (
      "https://cloud.google.com/dataform/reference/rest/"
      "v1beta1/projects.locations.repositories"
  )
  description = "Dataform Repository resources."

  def build_get_request(self) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesGetRequest(
        name=self._get_resource_name()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesCreateRequest(
        parent=self._get_parent_path(),
        repository=resource_message,
        repositoryId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    resource_message.name = existing_resource.name
    return self.messages.DataformProjectsLocationsRepositoriesPatchRequest(
        name=existing_resource.name,
        repository=resource_message,
        updateMask=",".join(changed_fields),
    )


class DataformReleaseConfigHandler(base.GcpResourceHandler):
  """Handler for Dataform ReleaseConfig resources."""

  _documentation_uri = (
      "https://cloud.google.com/dataform/reference/rest/"
      "v1beta1/projects.locations.repositories.releaseConfigs"
  )
  description = (
      "Dataform ReleaseConfig resources.\n"
      "Special handling:\n"
      " - releaseCompilationResult: setting to 'auto' in definition triggers "
      "compilation after resource creation or update"
  )

  def build_get_request(self) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesReleaseConfigsGetRequest(
        name=self._get_resource_name()
    )

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesReleaseConfigsCreateRequest(
        parent=self._get_parent_path(),
        releaseConfig=resource_message,
        releaseConfigId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    resource_message.name = existing_resource.name
    return self.messages.DataformProjectsLocationsRepositoriesReleaseConfigsPatchRequest(
        name=existing_resource.name,
        releaseConfig=resource_message,
        updateMask=",".join(changed_fields),
    )

  def get_local_definition(self) -> Dict[str, Any]:
    definition = super().get_local_definition()
    if "releaseCompilationResult" in definition:
      self._release_compilation_result = definition.pop(
          "releaseCompilationResult"
      )
    return definition

  def compare(
      self, existing_resource: Any, local_definition: dict[str, Any]
  ) -> list[str]:
    diffs = super().compare(existing_resource, local_definition)
    if diffs:
      return diffs

    if getattr(self, "_release_compilation_result", None) == "auto":
      existing_dict = existing_resource
      if not isinstance(existing_resource, dict):
        existing_dict = encoding.MessageToDict(existing_resource)

      compilation_result_name = existing_dict.get("releaseCompilationResult")
      if not compilation_result_name:
        log.status.Print(
            "     [+] Server has no compilation result. Forcing compilation..."
        )
        return ["releaseCompilationResult"]

      # Fetch compilation result to verify commit
      try:
        get_request_type = (
            self.messages.DataformProjectsLocationsRepositoriesCompilationResultsGetRequest
        )
        get_request = get_request_type(name=compilation_result_name)
        compilation_result = (
            self.client.projects_locations_repositories_compilationResults.Get(
                get_request
            )
        )

        if compilation_result.compilationErrors:
          log.status.Print(
              f"     [+] Found {len(compilation_result.compilationErrors)} "
              "compilation errors in existing results. Forcing recompilation..."
          )
          return ["releaseCompilationResult"]

        expected_commit = local_definition.get("gitCommitish")
        server_commit = compilation_result.resolvedGitCommitSha

        # Clever compare (match short vs full)
        if server_commit and expected_commit:
          if (not server_commit.startswith(expected_commit) and
              not expected_commit.startswith(server_commit)):
            log.status.Print(
                f"     [+] Compilation commit {server_commit} != expected "
                f"{expected_commit}. Forcing recompilation..."
            )
            return ["releaseCompilationResult"]
      except Exception as e:  # pylint: disable=broad-except
        log.status.Print(
            f"     [!] Failed to verify compilation result: {e}. "
            "Forcing recompilation..."
        )
        return ["releaseCompilationResult"]

    return []

  def post_deploy(self, api_response: Any, created: bool) -> None:
    if getattr(self, "_release_compilation_result", None) == "auto":
      log.status.Print(
          f"     [+] Triggering compilation for release config "
          f"'{self.resource.name}'..."
      )
      request = self.messages.DataformProjectsLocationsRepositoriesCompilationResultsCreateRequest(
          parent=self._get_parent_path(),
          compilationResult=self.messages.CompilationResult(
              releaseConfig=self._get_resource_name()
          ),
      )
      compilation_result = (
          self.client.projects_locations_repositories_compilationResults.Create(
              request=request
          )
      )
      if compilation_result.compilationErrors:
        error_details = "\n".join([
            f"  - {err.path or 'Unknown file'}: {err.message}"
            for err in compilation_result.compilationErrors
        ])
        raise ValueError(
            "Dataform compilation failed with following errors:\n"
            f"{error_details}\nStopping deployment."
        )
      local_def = self.get_local_definition()
      git_commitish = local_def.get("gitCommitish")
      patch_request = self.messages.DataformProjectsLocationsRepositoriesReleaseConfigsPatchRequest(
          name=self._get_resource_name(),
          releaseConfig=self.messages.ReleaseConfig(
              releaseCompilationResult=compilation_result.name,
              gitCommitish=git_commitish
          ),
          updateMask="releaseCompilationResult",
      )
      self.client.projects_locations_repositories_releaseConfigs.Patch(
          request=patch_request
      )


class DataformWorkflowConfigHandler(base.GcpResourceHandler):
  """Handler for Dataform WorkflowConfig resources."""

  _documentation_uri = (
      "https://cloud.google.com/dataform/reference/rest/"
      "v1beta1/projects.locations.repositories.workflowConfigs"
  )
  description = (
      "Dataform WorkflowConfig resources.\n"
      "Definition handling:\n"
      " - releaseConfig: accepts short ID of config within the same "
      "repository instead of full URI"
  )

  def build_get_request(self) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesWorkflowConfigsGetRequest(
        name=self._get_resource_name()
    )

  def get_local_definition(self) -> Dict[str, Any]:
    definition = super().get_local_definition()
    if ("releaseConfig" in definition and
        "/" not in definition["releaseConfig"]):
      release_config_id = definition["releaseConfig"]
      definition["releaseConfig"] = (
          f"{self._get_parent_path()}/releaseConfigs/{release_config_id}"
      )
    return definition

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesWorkflowConfigsCreateRequest(
        parent=self._get_parent_path(),
        workflowConfig=resource_message,
        workflowConfigId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    resource_message.name = existing_resource.name
    return self.messages.DataformProjectsLocationsRepositoriesWorkflowConfigsPatchRequest(
        name=existing_resource.name,
        workflowConfig=resource_message,
        updateMask=",".join(changed_fields),
    )


class DataformWorkspaceHandler(base.GcpResourceHandler):
  """Handler for Dataform Workspace resources."""

  _documentation_uri = (
      "https://cloud.google.com/dataform/reference/rest/"
      "v1beta1/projects.locations.repositories.workspaces"
  )
  description = "Dataform Workspace resources."

  def build_get_request(self) -> messages.Message:
    req_cls = (
        self.messages.DataformProjectsLocationsRepositoriesWorkspacesGetRequest
    )
    return req_cls(name=self._get_resource_name())

  def build_create_request(
      self, resource_message: messages.Message
  ) -> messages.Message:
    return self.messages.DataformProjectsLocationsRepositoriesWorkspacesCreateRequest(
        parent=self._get_parent_path(),
        workspace=resource_message,
        workspaceId=self.get_resource_id(),
    )

  def build_update_request(
      self,
      existing_resource: messages.Message,
      resource_message: messages.Message,
      changed_fields: list[str],
  ) -> messages.Message:
    # Dataform Workspaces only support Create/Get/Delete according to API,
    # so we should error on update. Note: dataform v1beta1 might have different
    # methods but we fall back to generic approach. If Patch is unsupported
    # it will raise exception during execution.
    resource_message.name = existing_resource.name
    return self.messages.DataformProjectsLocationsRepositoriesWorkspacesPatchRequest(
        name=existing_resource.name,
        workspace=resource_message,
        updateMask=",".join(changed_fields),
    )
