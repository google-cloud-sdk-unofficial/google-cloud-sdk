# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""Utility functions for the KMS Inventory CLI."""


from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis

DEFAULT_API_NAME = 'kmsinventory'
DEFAULT_API_VERSION = 'v1'


# The messages module can also be accessed from client.MESSAGES_MODULE
def GetClientInstance():
  return apis.GetClientInstance(DEFAULT_API_NAME, DEFAULT_API_VERSION)


def GetMessagesModule():
  return apis.GetMessagesModule(DEFAULT_API_NAME, DEFAULT_API_VERSION)


def ListKeys(project, args):
  client = GetClientInstance()
  request = GetMessagesModule().KmsinventoryProjectsCryptoKeysListRequest(
      parent='projects/' + project)

  return list_pager.YieldFromList(
      client.projects_cryptoKeys,
      request,
      limit=args.limit,
      batch_size_attribute='pageSize',
      batch_size=args.page_size,
      field='cryptoKeys')


def GetProtectedResourcesSummary(name, fallback_scope=None):
  """Gets a summary of protected resources for a given CryptoKey.

  Args:
    name: The resource name of the CryptoKey.
    fallback_scope: Optional. The scope to fall back to if the summary cannot
      be generated for the specified CryptoKey.

  Returns:
    A ProtectedResourcesSummary message.
  """
  client = GetClientInstance()
  messages = GetMessagesModule()
  fallback_scope_enum = None
  if fallback_scope is not None:
    fallback_scope_enum = (
        messages.KmsinventoryProjectsLocationsKeyRingsCryptoKeysGetProtectedResourcesSummaryRequest.FallbackScopeValueValuesEnum(
            fallback_scope
        )
    )
  request = messages.KmsinventoryProjectsLocationsKeyRingsCryptoKeysGetProtectedResourcesSummaryRequest(
      name=name,
      fallbackScope=fallback_scope_enum
  )
  return client.projects_locations_keyRings_cryptoKeys.GetProtectedResourcesSummary(
      request
  )


def SearchProtectedResources(scope, key_name, resource_types, args):
  client = GetClientInstance()
  request = GetMessagesModule().KmsinventoryOrganizationsProtectedResourcesSearchRequest(
      scope=scope, cryptoKey=key_name, resourceTypes=resource_types
  )

  return list_pager.YieldFromList(
      client.organizations_protectedResources,
      request,
      method='Search',
      limit=args.limit,
      batch_size_attribute='pageSize',
      batch_size=args.page_size,
      field='protectedResources',
  )


# TODO: b/465667614 - Remove old function and rephrase function name and
# comments while doing GA.
# This new version allows the user to use project ID or project number as the
# scope and is only available in alpha.
# This function would be gradually propagated to beta and will be used in place
# of the old version in ga.
def SearchProtectedResourcesNew(scope, key_name, resource_types, args):
  """Searches for protected resources within a given scope.

  Args:
    scope: The scope of the search, can be 'organizations/ORG_ID' or
      'projects/PROJECT_ID'.
    key_name: The name of the crypto key.
    resource_types: A list of resource types to filter the search.
    args: The command line arguments, including limit and page_size.

  Returns:
    A generator yielding protected resources.
  """
  client = GetClientInstance()
  if scope.startswith('projects/'):
    service = client.projects_protectedResources
    request = (
        GetMessagesModule().KmsinventoryProjectsProtectedResourcesSearchRequest(
            scope=scope, cryptoKey=key_name, resourceTypes=resource_types
        )
    )
  else:
    service = client.organizations_protectedResources
    request = GetMessagesModule().KmsinventoryOrganizationsProtectedResourcesSearchRequest(
        scope=scope, cryptoKey=key_name, resourceTypes=resource_types
    )

  return list_pager.YieldFromList(
      service,
      request,
      method='Search',
      limit=args.limit,
      batch_size_attribute='pageSize',
      batch_size=args.page_size,
      field='protectedResources',
  )
