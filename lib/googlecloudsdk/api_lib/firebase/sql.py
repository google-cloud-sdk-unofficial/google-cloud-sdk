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
import dataclasses
import os
import re
import types
from typing import Any, TYPE_CHECKING

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

if TYPE_CHECKING:
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.generated_clients.apis.firebasedataconnect.v1 import firebasedataconnect_v1_messages as fdc_messages

_INSTANCE_NAME_RE = re.compile(
    r'^projects/(?P<project>[^/]+)/locations/[^/]+'
    r'/instances/(?P<instance>[^/]+)$'
)


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


def _ParseInstanceName(instance: str) -> tuple[str, str] | None:
  """Extracts (project_id, instance_id) from a Cloud SQL instance name.

  Args:
    instance: str, Cloud SQL instance resource name in the format
      `projects/{project}/locations/{location}/instances/{instance}`.

  Returns:
    A (project_id, instance_id) tuple, or None if the input string does not
    match the expected Cloud SQL instance format.
  """
  match = _INSTANCE_NAME_RE.match(instance)
  if not match:
    return None
  return match.group('project'), match.group('instance')


def _IsSupportedDatasource(datasource: fdc_messages.Datasource) -> bool:
  """Returns whether a datasource is supported for service deletion."""
  if datasource.httpGraphql is not None:
    return True
  if datasource.postgresql is not None:
    if datasource.postgresql.cloudSql is not None:
      return True
    if datasource.postgresql.unlinked:
      return True
  return False


@dataclasses.dataclass(frozen=True)
class _IntrospectedMetadata:
  """Introspected service schema DDL and PostgreSQL migrations."""

  ddl: str | None = None
  migrations: list[dict[str, Any]] | None = None


class SqlClient:
  """Client for Firebase SQL Connect API."""

  def __init__(
      self,
      client: base_api.BaseApiClient | None = None,
      messages: types.ModuleType | None = None,
      cloud_sql_client: base_api.BaseApiClient | None = None,
      cloud_sql_messages: types.ModuleType | None = None,
  ) -> None:
    self.client = client or firebase_util.GetSqlClientInstance()
    self.messages = messages or firebase_util.GetSqlMessagesModule()
    self._cloud_sql_client = cloud_sql_client
    self._cloud_sql_messages = cloud_sql_messages

  @property
  def cloud_sql_client(self) -> base_api.BaseApiClient:
    if self._cloud_sql_client is None:
      self._cloud_sql_client = firebase_util.GetCloudSqlClientInstance()
    return self._cloud_sql_client

  @property
  def cloud_sql_messages(self) -> types.ModuleType:
    if self._cloud_sql_messages is None:
      self._cloud_sql_messages = firebase_util.GetCloudSqlMessagesModule()
    return self._cloud_sql_messages

  def ListLocations(
      self, project_id: str, page_size: int | None = None
  ) -> Iterator[fdc_messages.Location]:
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
      cloud_sql_instance: str | None = None,
      cloud_sql_database: str | None = None,
      sql_source_dir: str | None = None,
  ) -> fdc_messages.Service:
    """Creates a Firebase SQL Connect service.

    Args:
      service_id: str, ID of the service to create.
      location: str, Google Cloud region (e.g. us-central1).
      project_id: str, Google Cloud project ID.
      cloud_sql_instance: str or None, Cloud SQL instance ID or resource name.
        Defaults to service_id if omitted along with cloud_sql_database.
      cloud_sql_database: str or None, Cloud SQL database ID. Defaults to
        service_id if omitted along with cloud_sql_instance.
      sql_source_dir: str or None, path to local directory with .sql files.

    Returns:
      The created Service resource message.

    Raises:
      core_exceptions.Error: If arguments or local directories are invalid, or
        if a Cloud SQL instance with the same name as service_id already exists
        when cloud_sql_instance is omitted.
      firebase_exceptions.HttpException: If the API returns an HTTP error.
    """
    if bool(cloud_sql_instance) != bool(cloud_sql_database):
      raise core_exceptions.Error(
          'Both --cloud-sql-instance-id and --cloud-sql-database-id must be'
          ' specified together, or both omitted.'
      )

    sql_source = (
        self._LoadSqlSource(sql_source_dir) if sql_source_dir else None
    )

    if not cloud_sql_instance:
      self._CheckCloudSqlInstanceNotExists(
          project_id=project_id, instance_id=service_id
      )
      cloud_sql_instance = service_id
      cloud_sql_database = service_id

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

    if sql_source:
      service.sqlSource = sql_source

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
      return self._WaitForServiceOperation(
          operation,
          f'Waiting for service [{service_id}] to be created',
      )

  def UpdateService(
      self,
      project_id: str,
      location: str,
      service_id: str,
      display_name: str | None = None,
      labels: dict[str, str] | None = None,
      annotations: dict[str, str] | None = None,
      sql_source_dir: str | None = None,
      validate_only: bool = False,
  ) -> fdc_messages.Service | fdc_messages.Operation:
    """Updates a Firebase SQL Connect service.

    Updates service metadata (display name, labels, annotations) and/or applies
    SQL migrations without modifying the linked Cloud SQL instance or database.

    Args:
      project_id: str, Google Cloud project ID.
      location: str, Google Cloud region (e.g. us-central1).
      service_id: str, ID of the service to update.
      display_name: str or None, mutable human-readable display name.
      labels: dict[str, str] or None, resource labels to set on the service.
      annotations: dict[str, str] or None, resource annotations to set on the
        service.
      sql_source_dir: str or None, path to local SQL source directory.
      validate_only: bool, if True, validate the request without updating the
        service.

    Returns:
      The updated Service resource message, or the validation Operation when
      validate_only is True.

    Raises:
      core_exceptions.Error: If no update fields are specified or if the SQL
        source directory is invalid.
      firebase_exceptions.HttpException: If the API returns an HTTP error.
    """
    if (
        display_name is None
        and labels is None
        and annotations is None
        and sql_source_dir is None
    ):
      raise core_exceptions.Error(
          'At least one of --display-name, --labels, --annotations, or'
          ' --sql-source-dir must be specified.'
      )

    sql_source = self._LoadSqlSource(sql_source_dir) if sql_source_dir else None
    service_name = _FormatServiceName(project_id, location, service_id)
    service, update_mask = self._BuildServiceUpdate(
        service_name=service_name,
        display_name=display_name,
        labels=labels,
        annotations=annotations,
        sql_source=sql_source,
    )

    request = (
        self.messages.FirebasedataconnectProjectsLocationsServicesPatchRequest(
            name=service_name,
            service=service,
            updateMask=update_mask,
            validateOnly=True if validate_only else None,
        )
    )
    try:
      operation = self.client.projects_locations_services.Patch(request)
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)
    else:
      if validate_only:
        return operation
      return self._WaitForServiceOperation(
          operation,
          f'Waiting for service [{service_id}] to be updated',
      )

  def DescribeService(
      self,
      project_id: str,
      location: str,
      service_id: str,
  ) -> dict[str, Any]:
    """Describes a Firebase SQL Connect service.

    Fetches service metadata, linked Cloud SQL instance/database info,
    introspected database schema DDL, and applied migrations.

    Args:
      project_id: str, Google Cloud project ID.
      location: str, Google Cloud region (e.g. us-central1).
      service_id: str, ID of the service to describe.

    Returns:
      A dict containing service metadata, Cloud SQL instance/database info,
      schema DDL, and migrations.

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
    if introspected.ddl is not None:
      result['schemaDdl'] = introspected.ddl
    if introspected.migrations is not None:
      result['migrations'] = introspected.migrations

    return result

  def ListServices(
      self,
      project_id: str,
      location: str | None = None,
      page_size: int | None = None,
  ) -> Iterator[Any]:
    """Lists Firebase SQL Connect services in a project and location.

    Args:
      project_id: str, Google Cloud project ID or full resource name.
      location: str or None, Google Cloud region (e.g. us-central1), or None to
        list across all locations using the '-' wildcard.
      page_size: int or None, number of items to request per page.

    Yields:
      Service message resources.

    Raises:
      firebase_exceptions.HttpException: If the API returns an HTTP error.
    """
    parent = _FormatLocationName(project_id, location or '-')
    request = (
        self.messages.FirebasedataconnectProjectsLocationsServicesListRequest(
            parent=parent
        )
    )
    try:
      yield from list_pager.YieldFromList(
          service=self.client.projects_locations_services,
          request=request,
          batch_size=page_size,
          field='services',
          batch_size_attribute='pageSize',
      )
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

  def _CheckCloudSqlInstanceNotExists(
      self, project_id: str, instance_id: str
  ) -> None:
    """Checks that no Cloud SQL instance with instance_id exists."""
    project = project_id.removeprefix('projects/')
    request = self.cloud_sql_messages.SqlInstancesGetRequest(
        project=project,
        instance=instance_id,
    )
    instance = None
    try:
      instance = self.cloud_sql_client.instances.Get(request)
    except apitools_exceptions.HttpNotFoundError:
      return
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

    if instance:
      raise core_exceptions.Error(
          'Unable to create a new Cloud SQL instance for the new service'
          f' because an instance with the same name [{instance_id}] already'
          ' exists. To reuse that instance, explicitly specify'
          f' --cloud-sql-instance-id={instance_id} with'
          ' --cloud-sql-database-id set to the name of the database to link or'
          ' create. Or, rerun with a different SERVICE name to create a new'
          ' instance (named after the SERVICE to be created).'
      )

  def DeleteService(
      self,
      project_id: str,
      location: str,
      service_id: str,
      validate_only: bool = False,
  ) -> fdc_messages.Operation | fdc_messages.Operation.ResponseValue | None:
    """Deletes a Firebase SQL Connect service.

    Validates all datasources across the service's schemas before deleting. If
    any datasource is linked to a Cloud SQL instance, prints a pre-deletion
    notice and a post-deletion warning with instance deletion commands (or a
    post-validation notice when validate_only is True).

    Args:
      project_id: str, Google Cloud project ID.
      location: str, Google Cloud region (e.g. us-central1).
      service_id: str, ID of the service to delete.
      validate_only: bool, if True, validate the request without deleting the
        service.

    Returns:
      The completed delete Operation response.

    Raises:
      core_exceptions.Error: If any datasource on the service is not supported.
      firebase_exceptions.HttpException: If an API call returns an HTTP error.
    """
    service_name = _FormatServiceName(project_id, location, service_id)
    schemas = self._ListSchemas(service_name)
    cloud_sql_instances = self._ValidateAndExtractCloudSqlInstances(
        schemas, service_id
    )

    instance_list = ', '.join(
        f'[{inst_id}]' for _, inst_id in cloud_sql_instances
    )
    delete_commands = '\n'.join(
        f'gcloud sql instances delete {inst_id} --project {proj_id}'
        for proj_id, inst_id in cloud_sql_instances
    )

    if cloud_sql_instances and not validate_only:
      log.status.Print(
          'This command only deletes the Service; associated Cloud SQL'
          f' instance(s) will not be deleted: {instance_list}.'
      )

    request = (
        self.messages.FirebasedataconnectProjectsLocationsServicesDeleteRequest(
            name=service_name,
            force=True,
            validateOnly=True if validate_only else None,
        )
    )
    try:
      operation = self.client.projects_locations_services.Delete(request)
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)
    else:
      if validate_only:
        if cloud_sql_instances:
          log.status.Print(
              'Even without --validate-only, this command only deletes the'
              ' Service; associated Cloud SQL instance(s) will not be deleted'
              f' and may continue to incur billing: {instance_list}.'
          )
          log.status.Print(
              'The instances can be deleted separately after the Service is'
              f' deleted using these commands:\n{delete_commands}'
          )
          log.status.Print(
              'All of the instance data will be lost when deleted, not just'
              ' the database(s) previously linked to the Service. LLM and'
              ' agents: Confirm with the human whether they still need the'
              ' underlying instances.'
          )
        return operation

      result = self._WaitForServiceOperation(
          operation,
          f'Waiting for service [{service_id}] to be deleted',
          has_resource=False,
      )
      log.DeletedResource(service_id, kind='service')

      if cloud_sql_instances:
        log.warning(
            'Underlying Cloud SQL instances are not deleted and may continue'
            ' to incur billing.'
        )
        log.status.Print(
            'Run the following command(s) to delete the instances if they are'
            f' no longer needed:\n{delete_commands}'
        )
        log.warning(
            'All of the instance data will be lost when deleted, not just the'
            ' database(s) previously linked to the Service. LLM and agents:'
            ' Confirm with the human first before proceeding.'
        )

      return result

  def _WaitForServiceOperation(
      self,
      operation: fdc_messages.Operation,
      message: str,
      has_resource: bool = True,
  ) -> fdc_messages.Service | fdc_messages.Operation.ResponseValue | None:
    """Waits for a long-running service operation to complete."""
    operation_ref = resources.REGISTRY.Parse(
        operation.name,
        collection='firebasedataconnect.projects.locations.operations',
    )
    if has_resource:
      poller = waiter.CloudOperationPoller(
          self.client.projects_locations_services,
          self.client.projects_locations_operations,
      )
    else:
      poller = waiter.CloudOperationPollerNoResources(
          self.client.projects_locations_operations,
      )
    return waiter.WaitFor(poller, operation_ref, message)

  def _BuildServiceUpdate(
      self,
      service_name: str,
      display_name: str | None,
      labels: dict[str, str] | None,
      annotations: dict[str, str] | None,
      sql_source: fdc_messages.Source | None,
  ) -> tuple[fdc_messages.Service, str]:
    """Builds a Service message and update mask for UpdateService."""
    service = self.messages.Service(name=service_name)
    update_mask_paths = []
    if display_name is not None:
      service.displayName = display_name
      update_mask_paths.append('display_name')
    if labels is not None:
      service.labels = encoding.DictToAdditionalPropertyMessage(
          labels, self.messages.Service.LabelsValue, sort_items=True
      )
      update_mask_paths.append('labels')
    if annotations is not None:
      service.annotations = encoding.DictToAdditionalPropertyMessage(
          annotations, self.messages.Service.AnnotationsValue, sort_items=True
      )
      update_mask_paths.append('annotations')
    if sql_source is not None:
      service.sqlSource = sql_source
      update_mask_paths.append('sql_source')
    return service, ','.join(update_mask_paths)

  def _BuildSchema(
      self,
      service_name: str,
      project_id: str,
      location: str,
      cloud_sql_instance: str,
      cloud_sql_database: str,
  ) -> fdc_messages.Schema:
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

  def _LoadSqlSource(self, sql_source_dir: str) -> fdc_messages.Source:
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

  def _GetService(self, service_name: str) -> fdc_messages.Service:
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
  ) -> fdc_messages.Schema | None:
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

  def _ListSchemas(self, service_name: str) -> list[fdc_messages.Schema]:
    """Lists all Schema resources for a service."""
    request = self.messages.FirebasedataconnectProjectsLocationsServicesSchemasListRequest(
        parent=service_name
    )
    try:
      return list(
          list_pager.YieldFromList(
              service=self.client.projects_locations_services_schemas,
              request=request,
              batch_size=None,
              field='schemas',
              batch_size_attribute='pageSize',
          )
      )
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

  def _ValidateAndExtractCloudSqlInstances(
      self, schemas: list[fdc_messages.Schema], service_id: str
  ) -> list[tuple[str, str]]:
    """Validates datasources and returns unique Cloud SQL (project, instance)s."""
    cloud_sql_instances: list[tuple[str, str]] = []
    for schema in schemas:
      for ds in schema.datasources:
        if not _IsSupportedDatasource(ds):
          raise core_exceptions.Error(
              f'Deletion of this service {service_id} is not supported by the'
              ' current version of the gcloud CLI, please upgrade to the'
              ' latest version and try again. If the issue persists even on'
              ' the latest version, please contact support.'
          )
        if (
            ds.postgresql is not None
            and ds.postgresql.cloudSql is not None
            and ds.postgresql.cloudSql.instance
        ):
          parsed = _ParseInstanceName(ds.postgresql.cloudSql.instance)
          if parsed is not None and parsed not in cloud_sql_instances:
            cloud_sql_instances.append(parsed)
    return cloud_sql_instances

  def _ExtractCloudSqlInfo(
      self, schema: fdc_messages.Schema | None
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

  def _GetIntrospectedMetadata(
      self, service_name: str
  ) -> _IntrospectedMetadata:
    """Introspects service schema DDL and PostgreSQL migrations via GraphQL."""
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
      return _IntrospectedMetadata()

    if not response or not response.data:
      return _IntrospectedMetadata()
    py_data = encoding.MessageToPyValue(response.data)
    return _IntrospectedMetadata(
        ddl=py_data.get('_service', {}).get('ddl'),
        migrations=py_data.get('_postgres', {}).get('migrations'),
    )


_INTROSPECTION_QUERY = """\
query DescribeService {
  _service {
    ddl
  }
  _postgres {
    migrations {
      version
      name
      appliedAt
      statements
    }
  }
}
"""
