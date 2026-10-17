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
"""CRM API Boundaries utilities."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis

API_VERSION = 'v3'


def BoundariesClient(api_version: str = API_VERSION):
  """Returns a client instance of the CRM Boundaries service.

  Args:
    api_version: The CRM API version to use.

  Returns:
    The Cloud Resource Manager client instance.
  """
  return apis.GetClientInstance('cloudresourcemanager', api_version)


def BoundariesMessages(api_version: str = API_VERSION):
  """Returns the messages module for the Boundaries service.

  Args:
    api_version: The CRM API version to use.

  Returns:
    The Cloud Resource Manager messages module.
  """
  return apis.GetMessagesModule('cloudresourcemanager', api_version)


def FoldersBoundariesService(api_version: str = API_VERSION):
  """Returns the folders boundaries service class.

  Args:
    api_version: The CRM API version to use.

  Returns:
    The folders boundaries service instance.
  """
  return BoundariesClient(api_version).folders_boundaries


def OrganizationsBoundariesService(api_version: str = API_VERSION):
  """Returns the organizations boundaries service class.

  Args:
    api_version: The CRM API version to use.

  Returns:
    The organizations boundaries service instance.
  """
  return BoundariesClient(api_version).organizations_boundaries


def GetBoundariesService(parent_or_name: str, api_version: str = API_VERSION):
  """Returns the boundaries service for the given parent or resource name.

  Args:
    parent_or_name: The parent or boundary resource name.
    api_version: The CRM API version to use.

  Returns:
    The organizations or folders boundaries service instance.
  """
  if parent_or_name.startswith('organizations/'):
    return OrganizationsBoundariesService(api_version)
  return FoldersBoundariesService(api_version)


def CreateBoundary(
    parent: str,
    boundary_id: str,
    tag_key: str | None = None,
    tag_value: str | None = None,
    display_name: str | None = None,
    api_version: str = API_VERSION,
):
  """Creates a new Boundary under a folder or organization parent.

  Args:
    parent: The parent resource name (e.g. 'organizations/123' or
      'folders/456').
    boundary_id: The ID of the boundary to create.
    tag_key: Optional namespaced name of the tag key.
    tag_value: Optional short name of the tag value.
    display_name: Optional friendly display name for the boundary.
    api_version: The CRM API version to use.

  Returns:
    The Operation message representing the long-running create operation.
  """
  messages = BoundariesMessages(api_version)
  resource_filter = None
  if tag_key is not None or tag_value is not None:
    resource_filter = messages.ResourceFilter(
        tagFilter=messages.TagFilter(tagKey=tag_key, tagValue=tag_value)
    )
  boundary = messages.Boundary(
      name=f'{parent}/boundaries/{boundary_id}',
      displayName=display_name,
      resourceFilter=resource_filter,
  )
  if parent.startswith('organizations/'):
    return OrganizationsBoundariesService(api_version).Create(
        messages.CloudresourcemanagerOrganizationsBoundariesCreateRequest(
            parent=parent,
            boundaryId=boundary_id,
            boundary=boundary,
        )
    )
  return FoldersBoundariesService(api_version).Create(
      messages.CloudresourcemanagerFoldersBoundariesCreateRequest(
          parent=parent,
          boundaryId=boundary_id,
          boundary=boundary,
      )
  )


def GetBoundary(boundary_name: str, api_version: str = API_VERSION):
  """Gets a Boundary by its full resource name.

  Args:
    boundary_name: The full resource name of the Boundary (e.g.
      'organizations/123/boundaries/my-boundary' or
      'folders/456/boundaries/my-boundary').
    api_version: The CRM API version to use.

  Returns:
    The Boundary message.
  """
  messages = BoundariesMessages(api_version)
  if boundary_name.startswith('organizations/'):
    return OrganizationsBoundariesService(api_version).Get(
        messages.CloudresourcemanagerOrganizationsBoundariesGetRequest(
            name=boundary_name
        )
    )
  return FoldersBoundariesService(api_version).Get(
      messages.CloudresourcemanagerFoldersBoundariesGetRequest(
          name=boundary_name
      )
  )


def ListBoundaries(
    parent: str,
    page_size: int | None = None,
    api_version: str = API_VERSION,
):
  """Lists Boundaries under a folder or organization parent.

  Args:
    parent: The parent resource name (e.g. 'organizations/123' or
      'folders/456').
    page_size: Optional int, maximum number of boundaries per page.
    api_version: The CRM API version to use.

  Returns:
    A generator yielding Boundary messages.
  """
  messages = BoundariesMessages(api_version)
  if parent.startswith('organizations/'):
    service = OrganizationsBoundariesService(api_version)
    request = messages.CloudresourcemanagerOrganizationsBoundariesListRequest(
        parent=parent
    )
  else:
    service = FoldersBoundariesService(api_version)
    request = messages.CloudresourcemanagerFoldersBoundariesListRequest(
        parent=parent
    )

  return list_pager.YieldFromList(
      service,
      request,
      batch_size_attribute='pageSize',
      batch_size=page_size,
      field='boundaries',
  )


def UpdateBoundary(
    boundary_name: str,
    display_name: str | None = None,
    tag_value: str | None = None,
    etag: str | None = None,
    api_version: str = API_VERSION,
):
  """Updates a Boundary.

  Args:
    boundary_name: The full resource name of the Boundary.
    display_name: Optional friendly display name.
    tag_value: Optional short name of the tag value.
    etag: Optional etag of the boundary.
    api_version: The CRM API version to use.

  Returns:
    The Operation message representing the long-running patch operation.
  """
  messages = BoundariesMessages(api_version)
  boundary = messages.Boundary()
  update_mask_fields = []

  if display_name is not None:
    boundary.displayName = display_name
    update_mask_fields.append('displayName')

  if tag_value is not None:
    boundary.resourceFilter = messages.ResourceFilter(
        tagFilter=messages.TagFilter(tagValue=tag_value)
    )
    update_mask_fields.append('resourceFilter.tagFilter.tagValue')

  if etag is not None:
    boundary.etag = etag

  update_mask = ','.join(update_mask_fields)

  if boundary_name.startswith('organizations/'):
    return OrganizationsBoundariesService(api_version).Patch(
        messages.CloudresourcemanagerOrganizationsBoundariesPatchRequest(
            name=boundary_name,
            boundary=boundary,
            updateMask=update_mask,
        )
    )
  return FoldersBoundariesService(api_version).Patch(
      messages.CloudresourcemanagerFoldersBoundariesPatchRequest(
          name=boundary_name,
          boundary=boundary,
          updateMask=update_mask,
      )
  )


def DeleteBoundary(
    boundary_name: str,
    api_version: str = API_VERSION,
):
  """Deletes a Boundary.

  Args:
    boundary_name: The full resource name of the Boundary.
    api_version: The CRM API version to use.

  Returns:
    The Operation message representing the long-running delete operation.
  """
  messages = BoundariesMessages(api_version)
  if boundary_name.startswith('organizations/'):
    return OrganizationsBoundariesService(api_version).Delete(
        messages.CloudresourcemanagerOrganizationsBoundariesDeleteRequest(
            name=boundary_name
        )
    )
  return FoldersBoundariesService(api_version).Delete(
      messages.CloudresourcemanagerFoldersBoundariesDeleteRequest(
          name=boundary_name
      )
  )
