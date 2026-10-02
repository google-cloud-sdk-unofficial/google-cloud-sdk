# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Database Migration Service conversion workspaces Base Client."""

import abc
from typing import Any, Iterable, Mapping, Optional

from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.generated_clients.apis.datamigration.v1 import datamigration_v1_client as client


class BaseConversionWorkspacesClient(abc.ABC):
  """Base Client for Conversion Workspaces APIs.

  This class is the base class for the conversion workspaces clients and
  provides the common services used by the clients in order to send API
  requests.

  Attributes:
    release_track: The release track of the client, controlling the API version
      to use.
    location: The location of the resources.
    client: The client used to send API requests.
    messages: The messages module used to construct API requests.
  """

  def __init__(
      self,
      release_track: base.ReleaseTrack,
      location: Optional[str] = None,
  ):
    """Initializes the instance with an API client based on the release track.

    Args:
      release_track: The release track of the client, controlling the API
        version to use.
      location: The location of the resources.
    """

    self.release_track = release_track

    self.client: client.DatamigrationV1 = api_util.GetClientInstance(
        release_track=release_track,
        location=location,
    )
    self.messages = api_util.GetMessagesModule(release_track=release_track)

  @property
  def cw_service(
      self,
  ) -> client.DatamigrationV1.ProjectsLocationsConversionWorkspacesService:
    """Returns the conversion workspaces service."""
    return self.client.projects_locations_conversionWorkspaces

  @property
  def mapping_rules_service(
      self,
  ) -> (
      client.DatamigrationV1.ProjectsLocationsConversionWorkspacesMappingRulesService
  ):
    """Returns the mapping rules service."""
    return self.client.projects_locations_conversionWorkspaces_mappingRules

  @property
  def location_service(
      self,
  ) -> client.DatamigrationV1.ProjectsLocationsService:
    """Returns the location service."""
    return self.client.projects_locations

  def ReadWorkspace(self, name: str):
    """Reads a conversion workspace resource."""
    return self.cw_service.Get(
        self.messages.DatamigrationProjectsLocationsConversionWorkspacesGetRequest(
            name=name,
        )
    )

  def GetGlobalFilter(self, name: str) -> str:
    """Get global filter for a conversion workspace.

    If no global filter is set, '*' will be returned.

    Args:
      name: The name of the conversion workspace.

    Returns:
      The global filter for the conversion workspace.
    """
    return self._GetAdditionalProperties(name).get('filter', '*')

  def _GetAdditionalProperties(self, name: str) -> Mapping[str, Any]:
    """Get conversion workspace additional properties.

    Args:
      name: The name of the conversion workspace.

    Returns:
      The conversion workspace additional properties.
    """
    conversion_workspace = self.ReadWorkspace(name=name)
    if not conversion_workspace.globalSettings:
      return {}

    return {
        additional_property.key: additional_property.value
        for additional_property in (
            conversion_workspace.globalSettings.additionalProperties
        )
    }

  def CombineFilters(
      self,
      *filter_exprs: Iterable[Optional[str]],
  ) -> Optional[str]:
    """Combine filter expression with global filter.

    Args:
      *filter_exprs: Filter expressions to combine.

    Returns:
      Combined filter expression (or None if no filter expressions are
      provided).
    """

    cleaned_filters = tuple(
        expr for expr in filter_exprs if expr and expr != '*'
    )

    if not cleaned_filters:
      return None
    if len(cleaned_filters) == 1:
      return cleaned_filters[0]

    return ' AND '.join(f'({expr})' for expr in cleaned_filters)
