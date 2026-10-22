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
"""API client helper for Firebase SQL Connect management."""

from __future__ import annotations

from collections.abc import Iterator
import os
import types
from typing import Any

from apitools.base.py import base_api
from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.firebase import util as firebase_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files


def _FormatProjectName(project_id: str) -> str:
  """Formats project ID into full resource name."""
  if project_id.startswith('projects/'):
    return project_id
  return f'projects/{project_id}'


def _FormatLocationName(project_id: str, location: str) -> str:
  """Formats location ID into full resource name."""
  if location.startswith('projects/'):
    return location
  return f'{_FormatProjectName(project_id)}/locations/{location}'


def _FormatServiceName(project_id: str, location: str, service_id: str) -> str:
  """Formats service ID into full resource name."""
  if service_id.startswith('projects/'):
    return service_id
  return f'{_FormatLocationName(project_id, location)}/services/{service_id}'


def _FormatInstanceName(
    project_id: str, location: str, instance_id: str
) -> str:
  """Formats Cloud SQL instance into full resource name."""
  if instance_id.startswith('projects/'):
    return instance_id
  return f'{_FormatLocationName(project_id, location)}/instances/{instance_id}'


class SqlClient:
  """Client for Firebase SQL Connect API."""

  def __init__(
      self,
      client: base_api.BaseApiClient | None = None,
      messages: types.ModuleType | None = None,
  ) -> None:
    self.client = client or firebase_util.GetSqlClientInstance()
    self.messages = messages or firebase_util.GetSqlMessagesModule()

  def ListLocations(
      self, project_id: str, page_size: int | None = None
  ) -> Iterator[Any]:
    """Lists available Firebase SQL Connect locations for a project.

    Args:
      project_id: str, Google Cloud project ID or full resource name.
      page_size: int or None, number of items to request per page.

    Yields:
      Location message resources.
    """
    parent = _FormatProjectName(project_id)
    request = self.messages.FirebasedataconnectProjectsLocationsListRequest(
        name=parent
    )
    try:
      yield from list_pager.YieldFromList(
          service=self.client.projects_locations,
          request=request,
          batch_size=page_size,
          field='locations',
          batch_size_attribute='pageSize',
      )
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

  def CreateService(
      self,
      service_id: str,
      location: str,
      project_id: str,
      cloud_sql_instance: str,
      cloud_sql_database: str,
      sql_source_dir: str | None = None,
  ) -> Any:
    """Creates a Firebase SQL Connect service.

    Args:
      service_id: str, ID of the service to create.
      location: str, Google Cloud region (e.g. us-central1).
      project_id: str, Google Cloud project ID.
      cloud_sql_instance: str, Cloud SQL instance ID or resource name.
      cloud_sql_database: str, Cloud SQL database ID.
      sql_source_dir: str or None, path to local directory with .sql files.

    Returns:
      The created Service resource message.

    Raises:
      core_exceptions.Error: If arguments or local directories are invalid.
      firebase_exceptions.HttpException: If the API returns an HTTP error.
    """
    parent = _FormatLocationName(project_id, location)
    service_name = _FormatServiceName(project_id, location, service_id)
    service = self.messages.Service(
        name=service_name,
        schemas=[
            self._BuildSchema(
                service_name=service_name,
                project_id=project_id,
                location=location,
                cloud_sql_instance=cloud_sql_instance,
                cloud_sql_database=cloud_sql_database,
            )
        ],
    )

    if sql_source_dir:
      service.sqlSource = self._LoadSqlSource(sql_source_dir)

    request = (
        self.messages.FirebasedataconnectProjectsLocationsServicesCreateRequest(
            parent=parent,
            serviceId=service_id,
            service=service,
        )
    )
    try:
      operation = self.client.projects_locations_services.Create(request)
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)
    else:
      operation_ref = resources.REGISTRY.Parse(
          operation.name,
          collection='firebasedataconnect.projects.locations.operations',
      )
      poller = waiter.CloudOperationPoller(
          self.client.projects_locations_services,
          self.client.projects_locations_operations,
      )
      return waiter.WaitFor(
          poller,
          operation_ref,
          f'Waiting for service [{service_id}] to be created',
      )

  def DescribeService(
      self,
      project_id: str,
      location: str,
      service_id: str,
  ) -> dict[str, Any]:
    """Describes a Firebase SQL Connect service.

    Fetches service metadata, linked Cloud SQL instance/database info,
    introspected database schema tables, RLS policies, and applied migrations.

    Args:
      project_id: str, Google Cloud project ID.
      location: str, Google Cloud region (e.g. us-central1).
      service_id: str, ID of the service to describe.

    Returns:
      A dict containing service metadata, Cloud SQL instance/database info,
      schema tables, RLS policies, and migrations.

    Raises:
      firebase_exceptions.HttpException: If fetching the service fails.
    """
    service_name = _FormatServiceName(project_id, location, service_id)
    service = self._GetService(service_name)
    schema = self._GetSchema(service_name)
    csql_instance, database = self._ExtractCloudSqlInfo(schema)
    introspected = self._GetIntrospectedMetadata(service_name)

    result = dict(encoding.MessageToPyValue(service))

    if csql_instance is not None:
      result['csqlInstanceId'] = csql_instance
    if database is not None:
      result['databaseId'] = database

    for key in ('tables', 'policies', 'migrations'):
      if key in introspected:
        result[key] = introspected[key]

    return result

  def _BuildSchema(
      self,
      service_name: str,
      project_id: str,
      location: str,
      cloud_sql_instance: str,
      cloud_sql_database: str,
  ) -> Any:
    """Builds a Schema message for a Firebase SQL Connect service.

    Args:
      service_name: str, full resource name of the service.
      project_id: str, Google Cloud project ID.
      location: str, Google Cloud region (e.g. us-central1).
      cloud_sql_instance: str, Cloud SQL instance ID or resource name.
      cloud_sql_database: str, Cloud SQL database ID.

    Returns:
      A Schema message configured with a Cloud SQL datasource.
    """
    instance_name = _FormatInstanceName(
        project_id, location, cloud_sql_instance
    )
    postgresql = self.messages.PostgreSql(
        database=cloud_sql_database,
        cloudSql=self.messages.CloudSqlInstance(instance=instance_name),
    )
    return self.messages.Schema(
        name=f'{service_name}/schemas/main',
        datasources=[self.messages.Datasource(postgresql=postgresql)],
    )

  def _LoadSqlSource(self, sql_source_dir: str) -> Any:
    """Loads .sql files from a directory into a Source message.

    Args:
      sql_source_dir: str, path to local directory with .sql files.

    Returns:
      A Source message populated with File messages.

    Raises:
      core_exceptions.Error: If directory does not exist or contains no .sql
      files.
    """
    expanded_dir = os.path.abspath(os.path.expanduser(sql_source_dir))
    if not os.path.isdir(expanded_dir):
      raise core_exceptions.Error(
          f'SQL source directory [{sql_source_dir}] does not exist or is not a'
          ' directory.'
      )
    source_files = []
    for root, _, filenames in os.walk(expanded_dir):
      for filename in sorted(filenames):
        if filename.endswith('.sql'):
          full_path = os.path.join(root, filename)
          rel_path = os.path.relpath(full_path, expanded_dir).replace(
              os.sep, '/'
          )
          content = files.ReadFileContents(full_path)
          source_files.append(
              self.messages.File(path=rel_path, content=content)
          )
    if not source_files:
      raise core_exceptions.Error(
          f'No .sql files found in SQL source directory [{sql_source_dir}].'
      )
    source_files.sort(key=lambda f: f.path)
    return self.messages.Source(files=source_files)

  def _GetService(self, service_name: str) -> Any:
    """Fetches a Service resource by its full resource name."""
    request = (
        self.messages.FirebasedataconnectProjectsLocationsServicesGetRequest(
            name=service_name
        )
    )
    try:
      return self.client.projects_locations_services.Get(request)
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

  def _GetSchema(
      self, service_name: str, schema_id: str = 'main'
  ) -> Any | None:
    """Fetches a Schema resource for a service, or None if not found."""
    request = self.messages.FirebasedataconnectProjectsLocationsServicesSchemasGetRequest(
        name=f'{service_name}/schemas/{schema_id}'
    )
    try:
      return self.client.projects_locations_services_schemas.Get(request)
    except apitools_exceptions.HttpError as e:
      log.debug(
          'Failed to fetch schema [%s/schemas/%s]: %s',
          service_name,
          schema_id,
          e,
      )
      return None

  def _ExtractCloudSqlInfo(
      self, schema: Any | None
  ) -> tuple[str | None, str | None]:
    """Extracts Cloud SQL instance and database ID from a Schema resource."""
    if not schema or not schema.datasources:
      return None, None
    for ds in schema.datasources:
      if ds.postgresql:
        instance = (
            ds.postgresql.cloudSql.instance if ds.postgresql.cloudSql else None
        )
        return instance, ds.postgresql.database
    return None, None

  def _GetIntrospectedMetadata(self, service_name: str) -> dict[str, Any]:
    """Introspects PostgreSQL metadata for a service via GraphQL."""
    request = self.messages.FirebasedataconnectProjectsLocationsServicesIntrospectGraphqlRequest(
        name=service_name,
        graphqlRequest=self.messages.GraphqlRequest(query=_INTROSPECTION_QUERY),
    )
    try:
      response = self.client.projects_locations_services.IntrospectGraphql(
          request
      )
    except apitools_exceptions.HttpError as e:
      log.debug(
          'Failed to introspect metadata for service [%s]: %s',
          service_name,
          e,
      )
      return {}

    if not response or not response.data:
      return {}
    py_data = encoding.MessageToPyValue(response.data)
    return py_data.get('_postgres', {})


_INTROSPECTION_QUERY = """\
query DescribeService {
  _postgres {
    tables {
      id
      name
      schema
      owner
      rlsEnabled
      rlsForced
      replicaIdentity
      columns {
        name
        dataType
        nullable
        defaultValue
        isUnique
      }
      primaryKeys {
        name
        columns
      }
    }
    policies {
      id
      name
      schema
      table
      action
      roles
      command
      definition
      check
    }
    migrations {
      version
      name
      appliedAt
      statements
    }
  }
}
"""
