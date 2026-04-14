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
"""API client for Storage Intelligence Findings."""

from collections.abc import Iterator

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.generated_clients.apis.storage.v2 import storage_v2_messages

API_NAME = 'storage'
API_VERSION = 'v2'
PAGE_SIZE = 100


class IntelligenceFindingApi:
  """API client for intelligence findings.

  Attributes:
    client: The API client for interacting with the storage API.
    messages: The API messages for constructing requests and handling
      responses.
  """

  def __init__(self):
    self.client = apis.GetClientInstance(API_NAME, API_VERSION)
    self.messages = apis.GetMessagesModule(API_NAME, API_VERSION)
    self._services = {
        'projects': self.client.projects_locations_intelligenceFindings,
        'folders': self.client.folders_locations_intelligenceFindings,
        'organizations': (
            self.client.organizations_locations_intelligenceFindings
        ),
    }
    self._revision_service = (
        self.client.projects_locations_intelligenceFindings_revisions
    )

  def get_finding(
      self,
      name: str,
  ) -> 'storage_v2_messages.IntelligenceFinding':
    """Gets an intelligence finding.

    Args:
      name: The full name of the finding resource. Format:
        projects/{project}/locations/{location}/intelligenceFindings/{finding}

    Returns:
      IntelligenceFinding message.
    """
    request = (
        self.messages.StorageProjectsLocationsIntelligenceFindingsGetRequest(
            name=name
        )
    )
    return self._services['projects'].Get(request)

  def list_findings(
      self,
      parent: str,
      page_size: int | None = None,
  ) -> Iterator['storage_v2_messages.IntelligenceFinding']:
    """Lists intelligence findings for a given project and location.

    Args:
      parent: The parent resource to list findings for. Format:
        projects/{project}/locations/{location}
      page_size: The maximum number of findings to return per page. If not
        specified, the default page size is 100.

    Returns:
      Generator of IntelligenceFinding messages.
    """
    request = (
        self.messages.StorageProjectsLocationsIntelligenceFindingsListRequest(
            parent=parent,
        )
    )
    return list_pager.YieldFromList(
        self._services['projects'],
        request,
        batch_size=page_size if page_size is not None else PAGE_SIZE,
        batch_size_attribute='pageSize',
        field='intelligenceFindings',
    )

  def summarize_findings(
      self,
      parent: str,
      resource_scope: str | None = None,
      page_size: int | None = None,
  ) -> Iterator['storage_v2_messages.FindingSummary']:
    """Summarizes intelligence findings for a given scope.

    Args:
      parent: The scope to summarize findings for. Format:
        projects/{project}/locations/{location},
        folders/{folder}/locations/{location}, or
        organizations/{organization}/locations/{location}
      resource_scope: Granularity of findings (e.g., 'PARENT', 'PROJECT').
      page_size: The maximum number of findings to return per page. If not
        specified, the default page size is 100.

    Returns:
      Generator of FindingSummary messages.
    """
    scope_type = parent.split('/')[0]
    request_map = {
        'projects': (
            self.messages.StorageProjectsLocationsIntelligenceFindingsSummarizeRequest
        ),
        'folders': (
            self.messages.StorageFoldersLocationsIntelligenceFindingsSummarizeRequest
        ),
        'organizations': (
            self.messages.StorageOrganizationsLocationsIntelligenceFindingsSummarizeRequest
        ),
    }
    if scope_type not in request_map:
      raise exceptions.InvalidArgumentException(
          'parent',
          'Parent must be of the form projects/{project}/locations/{location}, '
          'folders/{folder}/locations/{location}, or '
          'organizations/{organization}/locations/{location} '
          f'but got {parent!r}',
      )

    request_type = request_map[scope_type]
    resource_scope_enum = (
        request_type.ResourceScopeValueValuesEnum(resource_scope)
        if resource_scope
        else None
    )
    request = request_type(
        parent=parent,
        resourceScope=resource_scope_enum,
    )
    return list_pager.YieldFromList(
        self._services[scope_type],
        request,
        batch_size=page_size if page_size is not None else PAGE_SIZE,
        batch_size_attribute='pageSize',
        field='findingSummaries',
        method='Summarize',
    )

  def get_revision(
      self,
      revision_name: str,
  ) -> 'storage_v2_messages.IntelligenceFindingRevision':
    """Gets an intelligence finding revision.

    Args:
      revision_name: The full name of the revision resource. Format:
        projects/{project}/locations/{location}/intelligenceFindings/{finding}/revisions/{revision}

    Returns:
      IntelligenceFindingRevision message.
    """
    request = self.messages.StorageProjectsLocationsIntelligenceFindingsRevisionsGetRequest(
        name=revision_name
    )
    return self._revision_service.Get(request)

  def list_revisions(
      self,
      parent: str,
      page_size: int | None = None,
  ) -> Iterator['storage_v2_messages.IntelligenceFindingRevision']:
    """Lists intelligence finding revisions for a given finding.

    Args:
      parent: The parent resource to list revisions for. Format:
        projects/{project}/locations/{location}/intelligenceFindings/{finding}
      page_size: The maximum number of revisions to return per page. If not
        specified, the default page size is 100.

    Returns:
      Generator of IntelligenceFindingRevision messages.
    """
    request = self.messages.StorageProjectsLocationsIntelligenceFindingsRevisionsListRequest(
        parent=parent,
    )
    return list_pager.YieldFromList(
        self._revision_service,
        request,
        batch_size=page_size if page_size is not None else PAGE_SIZE,
        batch_size_attribute='pageSize',
        field='intelligenceFindingRevisions',
    )
