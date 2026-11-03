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
"""CRM API Semantic Tags utilities."""

from collections.abc import Iterator, Mapping
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.generated_clients.apis.cloudresourcemanager.v3 import cloudresourcemanager_v3_client
from googlecloudsdk.generated_clients.apis.cloudresourcemanager.v3 import cloudresourcemanager_v3_messages

API_NAME = 'cloudresourcemanager'
API_VERSION = 'v3'


def SemanticTagsClient(api_version: str = API_VERSION):
  """Returns a client instance of the CRM Semantic Tags service.

  Args:
    api_version: The CRM API version to use.

  Returns:
    The Cloud Resource Manager client instance.
  """
  return apis.GetClientInstance(API_NAME, api_version)


def SemanticTagsMessages(api_version: str = API_VERSION):
  """Returns the messages module for the Semantic Tags service.

  Args:
    api_version: The CRM API version to use.

  Returns:
    The Cloud Resource Manager messages module.
  """
  return apis.GetMessagesModule(API_NAME, api_version)


def ProjectsSemanticTagKeysService(
    api_version: str = API_VERSION,
) -> (
    cloudresourcemanager_v3_client.CloudresourcemanagerV3.ProjectsLocationsSemanticTagKeysService
):
  """Returns the projects locations semanticTagKeys service instance."""
  return SemanticTagsClient(api_version).projects_locations_semanticTagKeys


def _SemanticTagKeyView(view: str | None, request_class):
  """Returns the request's `view` enum for a `basic` or `full` view name."""
  if not view:
    return None
  return request_class.ViewValueValuesEnum(
      f'SEMANTIC_TAG_KEY_VIEW_{view.upper()}'
  )


def GetSemanticTagKey(
    name: str, view: str | None = None, api_version: str = API_VERSION
) -> cloudresourcemanager_v3_messages.SemanticTagKey:
  """Gets a SemanticTagKey by its full resource name.

  Args:
    name: The full resource name of the SemanticTagKey (e.g.
      'projects/gcp-semantic-tags-catalog/locations/global/semanticTagKeys/'
      'placement').
    view: Optional level of detail, `basic` or `full`.
    api_version: The CRM API version to use.

  Returns:
    The SemanticTagKey message.
  """
  messages = SemanticTagsMessages(api_version)
  request_class = (
      messages.CloudresourcemanagerProjectsLocationsSemanticTagKeysGetRequest
  )
  return ProjectsSemanticTagKeysService(api_version).Get(
      request_class(name=name, view=_SemanticTagKeyView(view, request_class))
  )


def ListSemanticTagKeys(
    parent: str,
    filter_expr: str | None = None,
    view: str | None = None,
    page_size: int | None = None,
    api_version: str = API_VERSION,
) -> Iterator[cloudresourcemanager_v3_messages.SemanticTagKey]:
  """Lists SemanticTagKeys in a catalog location.

  Args:
    parent: The catalog location resource name (e.g.
      'projects/gcp-semantic-tags-catalog/locations/global').
    filter_expr: Optional server-side filter expression.
    view: Optional level of detail, `basic` or `full`.
    page_size: Optional maximum number of keys per page.
    api_version: The CRM API version to use.

  Returns:
    A generator yielding SemanticTagKey messages.
  """
  messages = SemanticTagsMessages(api_version)
  request_class = (
      messages.CloudresourcemanagerProjectsLocationsSemanticTagKeysListRequest
  )
  return list_pager.YieldFromList(
      ProjectsSemanticTagKeysService(api_version),
      request_class(
          parent=parent,
          filter=filter_expr,
          view=_SemanticTagKeyView(view, request_class),
      ),
      batch_size_attribute='pageSize',
      batch_size=page_size,
      field='semanticTagKeys',
  )


def OrganizationsSemanticTagValuesService(api_version: str = API_VERSION):
  """Returns the organizations locations semanticTagValues service instance."""
  return SemanticTagsClient(
      api_version
  ).organizations_locations_semanticTagValues


def ProjectsSemanticTagValuesService(api_version: str = API_VERSION):
  """Returns the projects locations semanticTagValues service instance."""
  return SemanticTagsClient(api_version).projects_locations_semanticTagValues


def GetSemanticTagValuesService(
    parent_or_name: str, api_version: str = API_VERSION
):
  """Returns the semanticTagValues service for the given parent or resource name.

  Args:
    parent_or_name: The parent or SemanticTagValue resource name.
    api_version: The CRM API version to use.

  Returns:
    The organizations or projects semanticTagValues service instance.
  """
  if parent_or_name.startswith('organizations/'):
    return OrganizationsSemanticTagValuesService(api_version)
  return ProjectsSemanticTagValuesService(api_version)


def BuildCompositeValue(
    fields_dict: Mapping[str, str], api_version: str = API_VERSION
):
  """Builds a CompositeValue message from a mapping of field names to strings.

  Args:
    fields_dict: Mapping of composite field names to string values.
    api_version: The CRM API version to use.

  Returns:
    A CompositeValue message.
  """
  messages = SemanticTagsMessages(api_version)
  additional_properties = [
      messages.CompositeValue.FieldsValue.AdditionalProperty(
          key=str(key),
          value=messages.FieldValue(stringValue=str(val)),
      )
      for key, val in sorted(fields_dict.items())
  ]
  return messages.CompositeValue(
      fields=messages.CompositeValue.FieldsValue(
          additionalProperties=additional_properties
      )
  )


def CreateSemanticTagValue(
    parent: str,
    value_id: str,
    semantic_tag_key: str,
    string_value: str | None = None,
    composite_fields: Mapping[str, str] | None = None,
    display_name: str | None = None,
    description: str | None = None,
    validate_only: bool = False,
    api_version: str = API_VERSION,
):
  """Creates a SemanticTagValue under an organization or project location.

  Args:
    parent: The parent location resource name (e.g.
      'organizations/123/locations/global' or
      'projects/my-proj/locations/global').
    value_id: The ID of the SemanticTagValue to create.
    semantic_tag_key: The full resource name of the associated SemanticTagKey.
    string_value: Optional scalar string value.
    composite_fields: Optional mapping of composite field names to string
      values.
    display_name: Optional user-friendly display name.
    description: Optional description of the SemanticTagValue.
    validate_only: Whether to only validate the request without creating the
      resource.
    api_version: The CRM API version to use.

  Returns:
    The Operation message representing the long-running create operation.
  """
  messages = SemanticTagsMessages(api_version)
  composite_value = None
  if composite_fields is not None:
    composite_value = BuildCompositeValue(composite_fields, api_version)

  semantic_tag_value = messages.SemanticTagValue(
      semanticTagKey=semantic_tag_key,
      stringValue=string_value,
      compositeValue=composite_value,
      displayName=display_name,
      description=description,
  )
  validate_only_param = True if validate_only else None

  if parent.startswith('organizations/'):
    return OrganizationsSemanticTagValuesService(api_version).Create(
        messages.CloudresourcemanagerOrganizationsLocationsSemanticTagValuesCreateRequest(
            parent=parent,
            semanticTagValueId=value_id,
            semanticTagValue=semantic_tag_value,
            validateOnly=validate_only_param,
        )
    )
  return ProjectsSemanticTagValuesService(api_version).Create(
      messages.CloudresourcemanagerProjectsLocationsSemanticTagValuesCreateRequest(
          parent=parent,
          semanticTagValueId=value_id,
          semanticTagValue=semantic_tag_value,
          validateOnly=validate_only_param,
      )
  )


def GetSemanticTagValue(name: str, api_version: str = API_VERSION):
  """Gets a SemanticTagValue by its full resource name.

  Args:
    name: The full resource name of the SemanticTagValue (e.g.
      'organizations/123/locations/global/semanticTagValues/val-1' or
      'projects/my-proj/locations/global/semanticTagValues/val-1').
    api_version: The CRM API version to use.

  Returns:
    The SemanticTagValue message.
  """
  messages = SemanticTagsMessages(api_version)
  if name.startswith('organizations/'):
    return OrganizationsSemanticTagValuesService(api_version).Get(
        messages.CloudresourcemanagerOrganizationsLocationsSemanticTagValuesGetRequest(
            name=name
        )
    )
  return ProjectsSemanticTagValuesService(api_version).Get(
      messages.CloudresourcemanagerProjectsLocationsSemanticTagValuesGetRequest(
          name=name
      )
  )


def ListSemanticTagValues(
    parent: str,
    filter_expr: str | None = None,
    page_size: int | None = None,
    api_version: str = API_VERSION,
):
  """Lists SemanticTagValues under an organization or project location.

  Args:
    parent: The parent location resource name (e.g.
      'organizations/123/locations/global' or
      'projects/my-proj/locations/global').
    filter_expr: Optional server-side filter expression.
    page_size: Optional maximum number of values per page.
    api_version: The CRM API version to use.

  Returns:
    A generator yielding SemanticTagValue messages.
  """
  messages = SemanticTagsMessages(api_version)
  if parent.startswith('organizations/'):
    service = OrganizationsSemanticTagValuesService(api_version)
    request = messages.CloudresourcemanagerOrganizationsLocationsSemanticTagValuesListRequest(
        parent=parent,
        filter=filter_expr,
    )
  else:
    service = ProjectsSemanticTagValuesService(api_version)
    request = messages.CloudresourcemanagerProjectsLocationsSemanticTagValuesListRequest(
        parent=parent,
        filter=filter_expr,
    )

  return list_pager.YieldFromList(
      service,
      request,
      batch_size_attribute='pageSize',
      batch_size=page_size,
      field='semanticTagValues',
  )


def OrganizationsSemanticTagBindingsService(
    api_version: str = API_VERSION,
) -> (
    cloudresourcemanager_v3_client.CloudresourcemanagerV3.OrganizationsLocationsSemanticTagBindingsService
):
  """Returns the organizations locations semanticTagBindings service instance."""
  return SemanticTagsClient(
      api_version
  ).organizations_locations_semanticTagBindings


def ProjectsSemanticTagBindingsService(
    api_version: str = API_VERSION,
) -> (
    cloudresourcemanager_v3_client.CloudresourcemanagerV3.ProjectsLocationsSemanticTagBindingsService
):
  """Returns the projects locations semanticTagBindings service instance."""
  return SemanticTagsClient(api_version).projects_locations_semanticTagBindings


# gcloud-disable-gdu-domain
def CreateSemanticTagBinding(
    parent: str,
    target_resource: str,
    semantic_tag_value: str,
    validate_only: bool = False,
    api_version: str = API_VERSION,
) -> cloudresourcemanager_v3_messages.Operation:
  """Creates a SemanticTagBinding under an organization or project location.

  Args:
    parent: The parent location resource name (e.g.
      'organizations/123/locations/global' or
      'projects/my-proj/locations/global').
    target_resource: Full resource name of the target Google Cloud resource
      being bound (e.g.
      '//compute.googleapis.com/projects/my-proj/zones/us-central1-a/instances/vm-1').
    semantic_tag_value: Full resource name of the SemanticTagValue being bound.
    validate_only: Whether to only validate the request without creating the
      binding.
    api_version: The CRM API version to use.

  Returns:
    The Operation message representing the long-running create operation.
  """
  messages = SemanticTagsMessages(api_version)
  semantic_tag_binding = messages.SemanticTagBinding(
      targetResource=target_resource,
      semanticTagValue=semantic_tag_value,
  )
  validate_only_param = True if validate_only else None

  if parent.startswith('organizations/'):
    return OrganizationsSemanticTagBindingsService(api_version).Create(
        messages.CloudresourcemanagerOrganizationsLocationsSemanticTagBindingsCreateRequest(
            parent=parent,
            semanticTagBinding=semantic_tag_binding,
            validateOnly=validate_only_param,
        )
    )
  return ProjectsSemanticTagBindingsService(api_version).Create(
      messages.CloudresourcemanagerProjectsLocationsSemanticTagBindingsCreateRequest(
          parent=parent,
          semanticTagBinding=semantic_tag_binding,
          validateOnly=validate_only_param,
      )
  )


def DeleteSemanticTagBinding(
    name: str,
    validate_only: bool = False,
    api_version: str = API_VERSION,
) -> cloudresourcemanager_v3_messages.Operation:
  """Deletes a SemanticTagBinding by its full resource name.

  Args:
    name: The full resource name of the SemanticTagBinding (e.g.
      'organizations/123/locations/global/semanticTagBindings/stb-1' or
      'projects/my-proj/locations/global/semanticTagBindings/stb-1').
    validate_only: Whether to only validate the request without deleting the
      binding.
    api_version: The CRM API version to use.

  Returns:
    The Operation message representing the long-running delete operation.
  """
  messages = SemanticTagsMessages(api_version)
  validate_only_param = True if validate_only else None
  if name.startswith('organizations/'):
    return OrganizationsSemanticTagBindingsService(api_version).Delete(
        messages.CloudresourcemanagerOrganizationsLocationsSemanticTagBindingsDeleteRequest(
            name=name,
            validateOnly=validate_only_param,
        )
    )
  return ProjectsSemanticTagBindingsService(api_version).Delete(
      messages.CloudresourcemanagerProjectsLocationsSemanticTagBindingsDeleteRequest(
          name=name,
          validateOnly=validate_only_param,
      )
  )


def ListSemanticTagBindings(
    parent: str,
    target_resource: str,
    filter_expr: str | None = None,
    page_size: int | None = None,
    api_version: str = API_VERSION,
) -> Iterator[cloudresourcemanager_v3_messages.SemanticTagBinding]:
  """Lists SemanticTagBindings under an organization or project location.

  Args:
    parent: The parent location resource name (e.g.
      'organizations/123/locations/global' or
      'projects/my-proj/locations/global').
    target_resource: Full resource name of the target Google Cloud resource
      whose bindings are being listed.
    filter_expr: Optional server-side filter expression.
    page_size: Optional maximum number of bindings per page.
    api_version: The CRM API version to use.

  Returns:
    A generator yielding SemanticTagBinding messages.
  """
  messages = SemanticTagsMessages(api_version)
  if parent.startswith('organizations/'):
    service = OrganizationsSemanticTagBindingsService(api_version)
    request = messages.CloudresourcemanagerOrganizationsLocationsSemanticTagBindingsListRequest(
        parent=parent,
        targetResource=target_resource,
        filter=filter_expr,
    )
  else:
    service = ProjectsSemanticTagBindingsService(api_version)
    request = messages.CloudresourcemanagerProjectsLocationsSemanticTagBindingsListRequest(
        parent=parent,
        targetResource=target_resource,
        filter=filter_expr,
    )

  return list_pager.YieldFromList(
      service,
      request,
      batch_size_attribute='pageSize',
      batch_size=page_size,
      field='semanticTagBindings',
  )
