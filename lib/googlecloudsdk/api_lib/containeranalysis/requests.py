# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utility for making containeranalysis API calls."""


import itertools

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources


def GetClient():
  return apis.GetClientInstance('containeranalysis', 'v1')


def GetMessages():
  return apis.GetMessagesModule('containeranalysis', 'v1')


def GetClientV1beta1():
  return apis.GetClientInstance('containeranalysis', 'v1beta1')


def GetMessagesV1beta1():
  return apis.GetMessagesModule('containeranalysis', 'v1beta1')


def ExportSbomV1beta1(project, uri):
  """Export SBOM for AR image resources."""
  client = GetClientV1beta1()

  # Workaround for apitools `{+name}` reserved expansion behavior:
  # apitools encodes `%` to `%25` for path parameters. To prevent Envoy/GFE
  # from collapsing double slashes, we pass encoded slashes in the path,
  # but apitools double-encodes them (e.g. `%3A%2F%2F` to `%253A%252F%252F`).
  # This hook intercepts the outgoing request and restores the single-encoded
  # slashes so Envoy doesn't collapse them.
  original_process_http_request = client.ProcessHttpRequest

  def CustomProcessHttpRequest(http_request):
    if 'https%253A%252F%252F' in http_request.url:
      http_request.url = http_request.url.replace(
          'https%253A%252F%252F', 'https%3A%2F%2F'
      )
    if 'http%253A%252F%252F' in http_request.url:
      http_request.url = http_request.url.replace(
          'http%253A%252F%252F', 'http%3A%2F%2F'
      )
    return original_process_http_request(http_request)

  client.ProcessHttpRequest = CustomProcessHttpRequest

  # Encode the scheme prefix (https:// or http://) to avoid double-slashes in
  # GFE/Envoy routing.
  if uri.startswith('https://'):
    encoded_uri = 'https%3A%2F%2F' + uri[8:]
  elif uri.startswith('http://'):
    encoded_uri = 'http%3A%2F%2F' + uri[7:]
  else:
    encoded_uri = uri

  messages = GetMessagesV1beta1()
  resource_ref = resources.REGISTRY.Create(
      'containeranalysis.projects.resources',
      projectsId=project,
      resourcesId=encoded_uri,
  )
  name = resource_ref.RelativeName()
  req = messages.ContaineranalysisProjectsResourcesExportSBOMRequest(name=name)
  return client.projects_resources.ExportSBOM(req)


def ListOccurrencesV1beta1(project, res_filter, page_size=1000):
  """List occurrences for resources in a project."""
  client = GetClientV1beta1()
  messages = GetMessagesV1beta1()
  project_ref = resources.REGISTRY.Parse(
      project, collection='cloudresourcemanager.projects'
  )
  return list_pager.YieldFromList(
      client.projects_occurrences,
      request=messages.ContaineranalysisProjectsOccurrencesListRequest(
          parent=project_ref.RelativeName(), filter=res_filter
      ),
      field='occurrences',
      batch_size=page_size,
      batch_size_attribute='pageSize',
  )


def ListOccurrencesWithFiltersV1beta1(project, filters):
  """List occurrences for resources in a project with multiple filters."""
  results = [ListOccurrencesV1beta1(project, f) for f in filters]
  return itertools.chain(*results)


def ListOccurrences(project, res_filter, page_size=1000):
  """List occurrences for resources in a project."""
  client = GetClient()
  messages = GetMessages()
  project_ref = resources.REGISTRY.Parse(
      project, collection='cloudresourcemanager.projects')
  return list_pager.YieldFromList(
      client.projects_occurrences,
      request=messages.ContaineranalysisProjectsOccurrencesListRequest(
          parent=project_ref.RelativeName(), filter=res_filter),
      field='occurrences',
      batch_size=page_size,
      batch_size_attribute='pageSize')


def ListOccurrencesWithFilters(project, filters):
  """List occurrences for resources in a project with multiple filters."""
  results = [ListOccurrences(project, f) for f in filters]
  return itertools.chain(*results)


def GetVulnerabilitySummary(project, res_filter):
  """Get vulnerability summary for resources in a project."""
  client = GetClient()
  messages = GetMessages()
  project_ref = resources.REGISTRY.Parse(
      project, collection='cloudresourcemanager.projects')
  req = (
      messages
      .ContaineranalysisProjectsOccurrencesGetVulnerabilitySummaryRequest(
          parent=project_ref.RelativeName(), filter=res_filter))
  return client.projects_occurrences.GetVulnerabilitySummary(req)


def GetVulnerabilitySummaryWithFilters(project, filters):
  """Get vulnerability summary for resources in a project with multiple filters."""
  return [GetVulnerabilitySummary(project, f) for f in filters]
