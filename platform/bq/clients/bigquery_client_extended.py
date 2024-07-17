#!/usr/bin/env python
"""BigqueryClientExtended class. Legacy code."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Any, Dict, List, Optional



# To configure apiclient logging.
from absl import flags

from clients import bigquery_client
from clients import client_dataset
from clients import client_job
from clients import table_reader as bq_table_reader
from clients import utils as bq_client_utils
from utils import bq_api_utils
from utils import bq_error
from utils import bq_id_utils
from utils import bq_processor_utils

Service = bq_api_utils.Service

# IAM role name that represents being a grantee on a row access policy.
_FILTERED_DATA_VIEWER_ROLE = 'roles/bigquery.filteredDataViewer'


class BigqueryClientExtended(bigquery_client.BigqueryClient):
  """Class extending BigqueryClient to add resource specific functionality."""


  def GetObjectInfo(self, reference):
    """Get all data returned by the server about a specific object."""
    # Projects are handled separately, because we only have
    # bigquery.projects.list.
    if isinstance(reference, bq_id_utils.ApiClientHelper.ProjectReference):
      max_project_results = 1000
      projects = self.ListProjects(max_results=max_project_results)
      for project in projects:
        if bq_processor_utils.ConstructObjectReference(project) == reference:
          project['kind'] = 'bigquery#project'
          return project
      if len(projects) >= max_project_results:
        raise bq_error.BigqueryError(
            'Number of projects found exceeded limit, please instead run'
            ' gcloud projects describe %s' % (reference,),
        )
      raise bq_error.BigqueryNotFoundError(
          'Unknown %r' % (reference,), {'reason': 'notFound'}, []
      )

    if isinstance(reference, bq_id_utils.ApiClientHelper.JobReference):
      return self.apiclient.jobs().get(**dict(reference)).execute()
    elif isinstance(reference, bq_id_utils.ApiClientHelper.DatasetReference):
      return self.apiclient.datasets().get(**dict(reference)).execute()
    elif isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
      return self.apiclient.tables().get(**dict(reference)).execute()
    elif isinstance(reference, bq_id_utils.ApiClientHelper.ModelReference):
      return (
          self.GetModelsApiClient()
          .models()
          .get(
              projectId=reference.projectId,
              datasetId=reference.datasetId,
              modelId=reference.modelId,
          )
          .execute()
      )
    elif isinstance(reference, bq_id_utils.ApiClientHelper.RoutineReference):
      return (
          self.GetRoutinesApiClient()
          .routines()
          .get(
              projectId=reference.projectId,
              datasetId=reference.datasetId,
              routineId=reference.routineId,
          )
          .execute()
      )
    else:
      raise TypeError(
          'Type of reference must be one of: ProjectReference, '
          'JobReference, DatasetReference, or TableReference'
      )

  def GetTableSchema(self, table_dict):
    table_info = self.apiclient.tables().get(**table_dict).execute()
    return table_info.get('schema', {})

  def InsertTableRows(
      self,
      table_dict: bq_id_utils.ApiClientHelper.TableReference,
      inserts: List[Optional[bq_processor_utils.InsertEntry]],
      skip_invalid_rows: Optional[bool] = None,
      ignore_unknown_values: Optional[bool] = None,
      template_suffix: Optional[int] = None,
  ):
    """Insert rows into a table.

    Arguments:
      table_dict: table reference into which rows are to be inserted.
      inserts: array of InsertEntry tuples where insert_id can be None.
      skip_invalid_rows: Optional. Attempt to insert any valid rows, even if
        invalid rows are present.
      ignore_unknown_values: Optional. Ignore any values in a row that are not
        present in the schema.
      template_suffix: Optional. The suffix used to generate the template
        table's name.

    Returns:
      result of the operation.
    """

    def _EncodeInsert(insert):
      encoded = dict(json=insert.record)
      if insert.insert_id:
        encoded['insertId'] = insert.insert_id
      return encoded

    op = (
        self.GetInsertApiClient()
        .tabledata()
        .insertAll(
            body=dict(
                skipInvalidRows=skip_invalid_rows,
                ignoreUnknownValues=ignore_unknown_values,
                templateSuffix=template_suffix,
                rows=list(map(_EncodeInsert, inserts)),
            ),
            **table_dict,
        )
    )
    return op.execute()

  def GetTransferConfig(self, transfer_id):
    client = self.GetTransferV1ApiClient()
    return (
        client.projects()
        .locations()
        .transferConfigs()
        .get(name=transfer_id)
        .execute()
    )

  def GetTransferRun(self, identifier):
    transfer_client = self.GetTransferV1ApiClient()
    return (
        transfer_client.projects()
        .locations()
        .transferConfigs()
        .runs()
        .get(name=identifier)
        .execute()
    )

  def ReadSchemaAndRows(
      self,
      table_ref: bq_id_utils.ApiClientHelper.TableReference,
      start_row: Optional[int] = None,
      max_rows: Optional[int] = None,
      selected_fields: Optional[str] = None,
  ):
    """Convenience method to get the schema and rows from a table.

    Arguments:
      table_ref: table reference.
      start_row: first row to read.
      max_rows: number of rows to read.
      selected_fields: a subset of fields to return.

    Returns:
      A tuple where the first item is the list of fields and the
      second item a list of rows.

    Raises:
      ValueError: will be raised if start_row is not explicitly provided.
      ValueError: will be raised if max_rows is not explicitly provided.
    """
    if start_row is None:
      raise ValueError('start_row is required')
    if max_rows is None:
      raise ValueError('max_rows is required')
    table_reader = bq_table_reader.TableTableReader(
        self.apiclient, self.max_rows_per_request, table_ref
    )
    return table_reader.ReadSchemaAndRows(
        start_row, max_rows, selected_fields=selected_fields
    )

  def ReadSchemaAndJobRows(
      self, job_dict, start_row=None, max_rows=None, result_first_page=None
  ):
    """Convenience method to get the schema and rows from job query result.

    Arguments:
      job_dict: job reference dictionary.
      start_row: first row to read.
      max_rows: number of rows to read.
      result_first_page: the first page of the result of a query job.

    Returns:
      A tuple where the first item is the list of fields and the
      second item a list of rows.
    Raises:
      ValueError: will be raised if start_row is not explicitly provided.
      ValueError: will be raised if max_rows is not explicitly provided.
    """
    if start_row is None:
      raise ValueError('start_row is required')
    if max_rows is None:
      raise ValueError('max_rows is required')
    if not job_dict:
      job_ref: bq_id_utils.ApiClientHelper.JobReference = None
    else:
      job_ref = bq_id_utils.ApiClientHelper.JobReference.Create(**job_dict)
    if flags.FLAGS.jobs_query_use_results_from_response and result_first_page:
      reader = bq_table_reader.QueryTableReader(
          self.apiclient, self.max_rows_per_request, job_ref, result_first_page
      )
    else:
      reader = bq_table_reader.JobTableReader(
          self.apiclient, self.max_rows_per_request, job_ref
      )
    return reader.ReadSchemaAndRows(start_row, max_rows)


  def ListProjectRefs(self, **kwds):
    """List the project references this user has access to."""
    return list(
        map(
            bq_processor_utils.ConstructObjectReference,
            self.ListProjects(**kwds),
        )
    )

  def ListProjects(self, max_results=None, page_token=None):
    """List the projects this user has access to."""
    request = bq_processor_utils.PrepareListRequest({}, max_results, page_token)
    result = self._ExecuteListProjectsRequest(request)
    results = result.get('projects', [])
    while 'nextPageToken' in result and (
        max_results is not None and len(results) < max_results
    ):
      request['pageToken'] = result['nextPageToken']
      result = self._ExecuteListProjectsRequest(request)
      results.extend(result.get('projects', []))
    return results

  def _ExecuteListProjectsRequest(self, request):
    return self.apiclient.projects().list(**request).execute()

  def ListDatasetRefs(self, **kwds):
    return list(
        map(
            bq_processor_utils.ConstructObjectReference,
            client_dataset.ListDatasets(
                self.apiclient,  # apiclient
                self,  # id_fallbacks
                **kwds,
            ),
        )
    )


  def ListTableRefs(self, **kwds):
    return list(
        map(
            bq_processor_utils.ConstructObjectReference, self.ListTables(**kwds)
        )
    )

  def ListTables(self, reference, max_results=None, page_token=None):
    """List the tables associated with this reference."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.DatasetReference,
        method='ListTables',
    )
    request = bq_processor_utils.PrepareListRequest(
        reference, max_results, page_token
    )
    result = self.apiclient.tables().list(**request).execute()
    results = result.get('tables', [])
    if max_results is not None:
      while 'nextPageToken' in result and len(results) < max_results:
        request['maxResults'] = max_results - len(results)
        request['pageToken'] = result['nextPageToken']
        result = self.apiclient.tables().list(**request).execute()
        results.extend(result.get('tables', []))
    return results

  def ListModels(self, reference, max_results, page_token):
    """Lists models for the given dataset reference.

    Arguments:
      reference: Reference to the dataset.
      max_results: Number of results to return.
      page_token: Token to retrieve the next page of results.

    Returns:
      A dict that contains entries:
        'results': a list of models
        'token': nextPageToken for the last page, if present.
    """
    return (
        self.GetModelsApiClient()
        .models()
        .list(
            projectId=reference.projectId,
            datasetId=reference.datasetId,
            maxResults=max_results,
            pageToken=page_token,
        )
        .execute()
    )

  def GetTableIAMPolicy(self, reference):
    """Gets IAM policy for the given table resource.

    Arguments:
      reference: the TableReference for the table resource.

    Returns:
      The IAM policy attached to the given table resource.

    Raises:
      TypeError: if reference is not a TableReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='GetTableIAMPolicy',
    )
    formatted_resource = 'projects/%s/datasets/%s/tables/%s' % (
        reference.projectId,
        reference.datasetId,
        reference.tableId,
    )
    return (
        self.GetIAMPolicyApiClient()
        .tables()
        .getIamPolicy(resource=formatted_resource)
        .execute()
    )

  def SetTableIAMPolicy(self, reference, policy):
    """Sets IAM policy for the given table resource.

    Arguments:
      reference: the TableReference for the table resource.
      policy: The policy string in JSON format.

    Returns:
      The updated IAM policy attached to the given table resource.

    Raises:
      TypeError: if reference is not a TableReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='SetTableIAMPolicy',
    )
    formatted_resource = 'projects/%s/datasets/%s/tables/%s' % (
        reference.projectId,
        reference.datasetId,
        reference.tableId,
    )
    request = {'policy': policy}
    return (
        self.GetIAMPolicyApiClient()
        .tables()
        .setIamPolicy(body=request, resource=formatted_resource)
        .execute()
    )

  #################################
  ## Table and dataset management
  #################################


  def GetTableRegion(
      self, reference: 'bq_id_utils.ApiClientHelper.TableReference'
  ) -> Optional[str]:
    """Returns the region of a table as a string."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='GetTableRegion',
    )
    try:
      return (
          self.apiclient.tables().get(**dict(reference)).execute()['location']
      )
    except bq_error.BigqueryNotFoundError:
      return None

  def TableExists(
      self, reference: 'bq_id_utils.ApiClientHelper.TableReference'
  ):
    """Returns true if the table exists."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='TableExists',
    )
    try:
      return self.apiclient.tables().get(**dict(reference)).execute()
    except bq_error.BigqueryNotFoundError:
      return False


  def ModelExists(
      self, reference: 'bq_id_utils.ApiClientHelper.ModelReference'
  ) -> bool:
    """Returns true if the model exists."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ModelReference,
        method='ModelExists',
    )
    try:
      return (
          self.GetModelsApiClient()
          .models()
          .get(
              projectId=reference.projectId,
              datasetId=reference.datasetId,
              modelId=reference.modelId,
          )
          .execute()
      )
    except bq_error.BigqueryNotFoundError:
      return False


  def CreateTable(
      self,
      reference,
      ignore_existing=False,
      schema=None,
      description=None,
      display_name=None,
      expiration=None,
      view_query=None,
      materialized_view_query=None,
      enable_refresh=None,
      refresh_interval_ms=None,
      max_staleness=None,
      external_data_config=None,
      biglake_config=None,
      view_udf_resources=None,
      use_legacy_sql=None,
      labels=None,
      time_partitioning=None,
      clustering=None,
      range_partitioning=None,
      require_partition_filter=None,
      destination_kms_key=None,
      location=None,
      table_constraints=None,
      resource_tags=None,
  ):
    """Create a table corresponding to TableReference.

    Args:
      reference: the TableReference to create.
      ignore_existing: (boolean, default False) If False, raise an exception if
        the dataset already exists.
      schema: an optional schema for tables.
      description: an optional description for tables or views.
      display_name: an optional friendly name for the table.
      expiration: optional expiration time in milliseconds since the epoch for
        tables or views.
      view_query: an optional Sql query for views.
      materialized_view_query: an optional standard SQL query for materialized
        views.
      enable_refresh: for materialized views, an optional toggle to enable /
        disable automatic refresh when the base table is updated.
      refresh_interval_ms: for materialized views, an optional maximum frequency
        for automatic refreshes.
      max_staleness: INTERVAL value that determines the maximum staleness
        allowed when querying a materialized view or an external table. By
        default no staleness is allowed.
      external_data_config: defines a set of external resources used to create
        an external table. For example, a BigQuery table backed by CSV files in
        GCS.
      biglake_config: specifies the configuration of a BigLake managed table.
      view_udf_resources: optional UDF resources used in a view.
      use_legacy_sql: The choice of using Legacy SQL for the query is optional.
        If not specified, the server will automatically determine the dialect
        based on query information, such as dialect prefixes. If no prefixes are
        found, it will default to Legacy SQL.
      labels: an optional dict of labels to set on the table.
      time_partitioning: if set, enables time based partitioning on the table
        and configures the partitioning.
      clustering: if set, enables and configures clustering on the table.
      range_partitioning: if set, enables range partitioning on the table and
        configures the partitioning.
      require_partition_filter: if set, partition filter is required for
        queiries over this table.
      destination_kms_key: User specified KMS key for encryption.
      location: an optional location for which to create tables or views.
      table_constraints: an optional primary key and foreign key configuration
        for the table.
      resource_tags: an optional dict of tags to attach to the table.

    Raises:
      TypeError: if reference is not a TableReference.
      BigqueryDuplicateError: if reference exists and ignore_existing
        is False.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='CreateTable',
    )

    try:
      body = bq_processor_utils.ConstructObjectInfo(reference)
      if schema is not None:
        body['schema'] = {'fields': schema}
      if display_name is not None:
        body['friendlyName'] = display_name
      if description is not None:
        body['description'] = description
      if expiration is not None:
        body['expirationTime'] = expiration
      if view_query is not None:
        view_args = {'query': view_query}
        if view_udf_resources is not None:
          view_args['userDefinedFunctionResources'] = view_udf_resources
        body['view'] = view_args
        if use_legacy_sql is not None:
          view_args['useLegacySql'] = use_legacy_sql
      if materialized_view_query is not None:
        materialized_view_args = {'query': materialized_view_query}
        if enable_refresh is not None:
          materialized_view_args['enableRefresh'] = enable_refresh
        if refresh_interval_ms is not None:
          materialized_view_args['refreshIntervalMs'] = refresh_interval_ms
        body['materializedView'] = materialized_view_args
      if external_data_config is not None:
        if max_staleness is not None:
          body['maxStaleness'] = max_staleness
        body['externalDataConfiguration'] = external_data_config
      if biglake_config is not None:
        body['biglakeConfiguration'] = biglake_config
      if labels is not None:
        body['labels'] = labels
      if time_partitioning is not None:
        body['timePartitioning'] = time_partitioning
      if clustering is not None:
        body['clustering'] = clustering
      if range_partitioning is not None:
        body['rangePartitioning'] = range_partitioning
      if require_partition_filter is not None:
        body['requirePartitionFilter'] = require_partition_filter
      if destination_kms_key is not None:
        body['encryptionConfiguration'] = {'kmsKeyName': destination_kms_key}
      if location is not None:
        body['location'] = location
      if table_constraints is not None:
        body['table_constraints'] = table_constraints
      if resource_tags is not None:
        body['resourceTags'] = resource_tags
      self.apiclient.tables().insert(
          body=body, **dict(reference.GetDatasetReference())
      ).execute()
    except bq_error.BigqueryDuplicateError:
      if not ignore_existing:
        raise


  def UpdateTable(
      self,
      reference,
      schema=None,
      description=None,
      display_name=None,
      expiration=None,
      view_query=None,
      materialized_view_query=None,
      enable_refresh=None,
      refresh_interval_ms=None,
      max_staleness=None,
      external_data_config=None,
      view_udf_resources=None,
      use_legacy_sql=None,
      labels_to_set=None,
      label_keys_to_remove=None,
      time_partitioning=None,
      range_partitioning=None,
      clustering=None,
      require_partition_filter=None,
      etag=None,
      encryption_configuration=None,
      location=None,
      autodetect_schema=False,
      table_constraints=None,
      tags_to_attach: Optional[Dict[str, str]] = None,
      tags_to_remove: Optional[List[str]] = None,
      clear_all_tags: bool = False,
  ):
    """Updates a table.

    Args:
      reference: the TableReference to update.
      schema: an optional schema for tables.
      description: an optional description for tables or views.
      display_name: an optional friendly name for the table.
      expiration: optional expiration time in milliseconds since the epoch for
        tables or views. Specifying 0 removes expiration time.
      view_query: an optional Sql query to update a view.
      materialized_view_query: an optional Standard SQL query for materialized
        views.
      enable_refresh: for materialized views, an optional toggle to enable /
        disable automatic refresh when the base table is updated.
      refresh_interval_ms: for materialized views, an optional maximum frequency
        for automatic refreshes.
      max_staleness: INTERVAL value that determines the maximum staleness
        allowed when querying a materialized view or an external table. By
        default no staleness is allowed.
      external_data_config: defines a set of external resources used to create
        an external table. For example, a BigQuery table backed by CSV files in
        GCS.
      view_udf_resources: optional UDF resources used in a view.
      use_legacy_sql: The choice of using Legacy SQL for the query is optional.
        If not specified, the server will automatically determine the dialect
        based on query information, such as dialect prefixes. If no prefixes are
        found, it will default to Legacy SQL.
      labels_to_set: an optional dict of labels to set on this table.
      label_keys_to_remove: an optional list of label keys to remove from this
        table.
      time_partitioning: if set, enables time based partitioning on the table
        and configures the partitioning.
      range_partitioning: if set, enables range partitioning on the table and
        configures the partitioning.
      clustering: if set, enables clustering on the table and configures the
        clustering spec.
      require_partition_filter: if set, partition filter is required for
        queiries over this table.
      etag: if set, checks that etag in the existing table matches.
      encryption_configuration: Updates the encryption configuration.
      location: an optional location for which to update tables or views.
      autodetect_schema: an optional flag to perform autodetect of file schema.
      table_constraints: an optional primary key and foreign key configuration
        for the table.
      tags_to_attach: an optional dict of tags to attach to the table
      tags_to_remove: an optional list of tag keys to remove from the table
      clear_all_tags: if set, clears all the tags attached to the table

    Raises:
      TypeError: if reference is not a TableReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='UpdateTable',
    )

    existing_table = {}
    if clear_all_tags:
      # getting existing table. This is required to clear all tags attached to
      # a table. Adding this at the start of the method as this can also be
      # used for other scenarios
      existing_table = self._ExecuteGetTableRequest(reference)
    table = bq_processor_utils.ConstructObjectInfo(reference)
    maybe_skip_schema = False
    if schema is not None:
      table['schema'] = {'fields': schema}
    elif not maybe_skip_schema:
      table['schema'] = None

    if encryption_configuration is not None:
      table['encryptionConfiguration'] = encryption_configuration
    if display_name is not None:
      table['friendlyName'] = display_name
    if description is not None:
      table['description'] = description
    if expiration is not None:
      if expiration == 0:
        table['expirationTime'] = None
      else:
        table['expirationTime'] = expiration
    if view_query is not None:
      view_args = {'query': view_query}
      if view_udf_resources is not None:
        view_args['userDefinedFunctionResources'] = view_udf_resources
      if use_legacy_sql is not None:
        view_args['useLegacySql'] = use_legacy_sql
      table['view'] = view_args
    materialized_view_args = {}
    if materialized_view_query is not None:
      materialized_view_args['query'] = materialized_view_query
    if enable_refresh is not None:
      materialized_view_args['enableRefresh'] = enable_refresh
    if refresh_interval_ms is not None:
      materialized_view_args['refreshIntervalMs'] = refresh_interval_ms
    if materialized_view_args:
      table['materializedView'] = materialized_view_args
    if external_data_config is not None:
      table['externalDataConfiguration'] = external_data_config
      if max_staleness is not None:
        table['maxStaleness'] = max_staleness
    if 'labels' not in table:
      table['labels'] = {}
    table_labels = table['labels']
    if table_labels is None:
      raise ValueError('Missing labels in table.')
    if labels_to_set:
      for label_key, label_value in labels_to_set.items():
        table_labels[label_key] = label_value
    if label_keys_to_remove:
      for label_key in label_keys_to_remove:
        table_labels[label_key] = None
    if time_partitioning is not None:
      table['timePartitioning'] = time_partitioning
    if range_partitioning is not None:
      table['rangePartitioning'] = range_partitioning
    if clustering is not None:
      if clustering == {}:  # pylint: disable=g-explicit-bool-comparison
        table['clustering'] = None
      else:
        table['clustering'] = clustering
    if require_partition_filter is not None:
      table['requirePartitionFilter'] = require_partition_filter
    if location is not None:
      table['location'] = location
    if table_constraints is not None:
      table['table_constraints'] = table_constraints
    resource_tags = {}
    if clear_all_tags and 'resourceTags' in existing_table:
      for tag in existing_table['resourceTags']:
        resource_tags[tag] = None
    else:
      for tag in tags_to_remove or []:
        resource_tags[tag] = None
    for tag in tags_to_attach or {}:
      resource_tags[tag] = tags_to_attach[tag]
    # resourceTags is used to add a new tag binding, update value of existing
    # tag and also to remove a tag binding
    # check go/bq-table-tags-api for details
    table['resourceTags'] = resource_tags
    self._ExecutePatchTableRequest(reference, table, autodetect_schema, etag)

  def _ExecuteGetTableRequest(self, reference):
    return self.apiclient.tables().get(**dict(reference)).execute()

  def _ExecutePatchTableRequest(
      self,
      reference,
      table,
      autodetect_schema: bool = False,
      etag: Optional[str] = None,
  ):
    """Executes request to patch table.

    Args:
      reference: the TableReference to patch.
      table: the body of request
      autodetect_schema: an optional flag to perform autodetect of file schema.
      etag: if set, checks that etag in the existing table matches.
    """
    request = self.apiclient.tables().patch(
        autodetect_schema=autodetect_schema, body=table, **dict(reference)
    )

    # Perform a conditional update to protect against concurrent
    # modifications to this table. If there is a conflicting
    # change, this update will fail with a "Precondition failed"
    # error.
    if etag:
      request.headers['If-Match'] = etag if etag else table['etag']
    request.execute()

  def UpdateModel(
      self,
      reference,
      description=None,
      expiration=None,
      labels_to_set=None,
      label_keys_to_remove=None,
      vertex_ai_model_id=None,
      etag=None,
  ):
    """Updates a Model.

    Args:
      reference: the ModelReference to update.
      description: an optional description for model.
      expiration: optional expiration time in milliseconds since the epoch.
        Specifying 0 clears the expiration time for the model.
      labels_to_set: an optional dict of labels to set on this model.
      label_keys_to_remove: an optional list of label keys to remove from this
        model.
      vertex_ai_model_id: an optional string as Vertex AI model ID to register.
      etag: if set, checks that etag in the existing model matches.

    Raises:
      TypeError: if reference is not a ModelReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ModelReference,
        method='UpdateModel',
    )

    updated_model = {}
    if description is not None:
      updated_model['description'] = description
    if expiration is not None:
      updated_model['expirationTime'] = expiration or None
    if 'labels' not in updated_model:
      updated_model['labels'] = {}
    if labels_to_set:
      for label_key, label_value in labels_to_set.items():
        updated_model['labels'][label_key] = label_value
    if label_keys_to_remove:
      for label_key in label_keys_to_remove:
        updated_model['labels'][label_key] = None
    if vertex_ai_model_id is not None:
      updated_model['trainingRuns'] = [
          {'vertex_ai_model_id': vertex_ai_model_id}
      ]

    request = (
        self.GetModelsApiClient()
        .models()
        .patch(
            body=updated_model,
            projectId=reference.projectId,
            datasetId=reference.datasetId,
            modelId=reference.modelId,
        )
    )

    # Perform a conditional update to protect against concurrent
    # modifications to this model. If there is a conflicting
    # change, this update will fail with a "Precondition failed"
    # error.
    if etag:
      request.headers['If-Match'] = etag if etag else updated_model['etag']
    request.execute()


  def DeleteTable(self, reference, ignore_not_found=False):
    """Deletes TableReference reference.

    Args:
      reference: the TableReference to delete.
      ignore_not_found: Whether to ignore "not found" errors.

    Raises:
      TypeError: if reference is not a TableReference.
      bq_error.BigqueryNotFoundError: if reference does not exist and
        ignore_not_found is False.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='DeleteTable',
    )
    try:
      self.apiclient.tables().delete(**dict(reference)).execute()
    except bq_error.BigqueryNotFoundError:
      if not ignore_not_found:
        raise


  def DeleteModel(self, reference, ignore_not_found=False):
    """Deletes ModelReference reference.

    Args:
      reference: the ModelReference to delete.
      ignore_not_found: Whether to ignore "not found" errors.

    Raises:
      TypeError: if reference is not a ModelReference.
      bq_error.BigqueryNotFoundError: if reference does not exist and
        ignore_not_found is False.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ModelReference,
        method='DeleteModel',
    )
    try:
      self.GetModelsApiClient().models().delete(
          projectId=reference.projectId,
          datasetId=reference.datasetId,
          modelId=reference.modelId,
      ).execute()
    except bq_error.BigqueryNotFoundError:
      if not ignore_not_found:
        raise


