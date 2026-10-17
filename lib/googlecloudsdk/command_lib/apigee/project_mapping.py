# -*- coding: utf-8 -*- # Lint as: python3
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
"""GCP project to Apigee organization mapping, caching, and location helpers."""

from collections.abc import Mapping
import os
from typing import Any

from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.command_lib.apigee import request
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


def _CachedDataWithName(name: str) -> dict[str, Any] | None:
  """Returns the contents of a named cache file.

  Cache files are saved as hidden YAML files in the gcloud config directory.

  Args:
    name: The name of the cache file.

  Returns:
    The decoded contents of the file, or an empty dictionary if the file could
    not be read for whatever reason.
  """
  config_dir = config.Paths().global_config_dir
  cache_path = os.path.join(config_dir, ".apigee-cached-" + name)
  if not os.path.isfile(cache_path):
    return {}
  try:
    return yaml.load_path(cache_path)
  except yaml.YAMLParseError:
    # Another gcloud command might be in the process of writing to the file.
    # Handle as a cache miss.
    return {}


def _SaveCachedDataWithName(data: dict[str, Any], name: str) -> None:
  """Saves `data` to a named cache file.

  Cache files are saved as hidden YAML files in the gcloud config directory.

  Args:
    data: The data to cache.
    name: The name of the cache file.
  """
  config_dir = config.Paths().global_config_dir
  cache_path = os.path.join(config_dir, ".apigee-cached-" + name)
  files.WriteFileContents(cache_path, yaml.dump(data))


def _DeleteCachedDataWithName(name: str) -> None:
  """Deletes a named cache file."""
  config_dir = config.Paths().global_config_dir
  cache_path = os.path.join(config_dir, ".apigee-cached-" + name)
  if os.path.isfile(cache_path):
    try:
      os.remove(cache_path)
    except OSError:
      return


def _GetProjectMappingFromApi(organization: str | None) -> dict[str, Any]:
  """Returns the project mapping for `organization` from the global endpoint."""
  try:
    return request.ResponseToApiRequest(
        {"organizationsId": organization},
        ["organization"],
        method=":getProjectMapping",
        method_override="GET",
        location="global",
    )
  except errors.RequestError as error:
    # Rewrite error message to better describe what was attempted.
    raise error.RewrittenError("project mapping", "get")


def _ListOrganizationsGlobal() -> dict[str, Any]:
  """Returns a list of Apigee organizations on the global endpoint."""
  try:
    return request.ResponseToApiRequest(
        identifiers=None,
        entity_path=[],
        entity_collection="organization",
        location="global",
    )
  except errors.RequestError as error:
    # Rewrite error message to better describe what was attempted.
    raise error.RewrittenError("organization", "list")


def GetProjectMapping(
    project: str | None, user_provided_org: str | None = None
) -> dict[str, Any] | None:
  """Returns the project mapping for the given GCP project.

  Args:
    project: The GCP project name.
    user_provided_org: The organization ID provided by the user, if any.

  Returns:
    The project mapping for the given GCP project.
  """

  project_mappings = _CachedDataWithName("project-mapping-v2") or {}

  if user_provided_org:
    mapping = project_mappings.get(user_provided_org, None)
    if mapping:
      return mapping
    else:
      try:
        project_mapping = _GetProjectMappingFromApi(user_provided_org)
      except (
          errors.EntityNotFoundError,
          errors.UnauthorizedRequestError,
      ) as exc:
        raise errors.UnauthorizedRequestError(
            message=(
                'Permission denied on resource "organizations/%s" (or it may'
                " not exist)"
            )
            % user_provided_org
        ) from exc
      except errors.RequestError as e:
        raise e

      if "organization" not in project_mapping:
        raise errors.UnauthorizedRequestError(
            message=(
                'Permission denied on resource "organizations/%s" (or it may'
                " not exist)"
            )
            % user_provided_org
        )

      project_mappings[project] = project_mapping
      _SaveCachedDataWithName(project_mappings, "project-mapping-v2")
      return project_mapping

  if project not in project_mappings:
    try:
      project_mapping = _GetProjectMappingFromApi(project)
    except (errors.EntityNotFoundError, errors.UnauthorizedRequestError):
      return None
    except errors.RequestError as e:
      raise e

    if "organization" not in project_mapping:
      return None

    if project_mapping.get("projectId", None) != project:
      return None

    project_mappings[project] = project_mapping
    _SaveCachedDataWithName(project_mappings, "project-mapping-v2")

  return project_mappings[project]


def FindMappingForProject(project: str | None) -> dict[str, Any] | None:
  """Returns the Apigee organization for the given GCP project."""
  project_mapping = _CachedDataWithName("project-mapping-v2") or {}

  if project in project_mapping:
    return project_mapping[project]

  # Listing organizations is an expensive operation for users with a lot of GCP
  # projects. Since the GCP project -> Apigee organization mapping is immutable
  # once created, cache known mappings to avoid the extra API call.
  overrides = properties.VALUES.api_endpoint_overrides.apigee.Get()
  if overrides:
    list_orgs = request.ResponseToApiRequest({}, [], "organization")
  else:
    list_orgs = _ListOrganizationsGlobal()

  for organization in list_orgs["organizations"]:
    for matching_project in organization["projectIds"]:
      project_mapping[matching_project] = {}
      project_mapping[matching_project] = organization
  _SaveCachedDataWithName(project_mapping, "project-mapping-v2")
  _DeleteCachedDataWithName("project-mapping")

  if project not in project_mapping:
    return None

  return project_mapping[project]


def GetOrganizationLocation(organization: str | None) -> str | None:
  """Returns the location of the Apigee organization."""
  project = properties.VALUES.core.project.Get()
  mapping = GetProjectMapping(project, organization)
  if mapping:
    return mapping.get("location", None)

  # Project mapping is not available, assume projectId is not same as
  # organization.
  mapping = FindMappingForProject(project)
  if mapping:
    return mapping.get("location", None)

  raise errors.LocationResolutionError()


def ResolveLocation(
    identifiers: Mapping[str, Any] | None,
) -> str | None:
  """Returns the location of the Apigee organization when not overridden."""
  if properties.VALUES.api_endpoint_overrides.apigee.Get():
    return None
  organization = (
      identifiers.get("organizationsId", None) if identifiers else None
  )
  return GetOrganizationLocation(organization)
