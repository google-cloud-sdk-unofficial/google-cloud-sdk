#!/usr/bin/env python
"""BigqueryClientExtended class. Legacy code."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import itertools
import logging
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional
import uuid



# To configure apiclient logging.
from absl import flags
from google.api_core.iam import Policy
from googleapiclient import http as http_request

from clients import bigquery_client
from clients import client_dataset
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

  #################################
  ## Utility methods
  #################################
  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTime(secs):
    return bq_client_utils.FormatTime(secs)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTimeFromProtoTimestampJsonString(json_string):
    """Converts google.protobuf.Timestamp formatted string to BQ format."""
    return bq_client_utils.FormatTimeFromProtoTimestampJsonString(json_string)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatAcl(acl):
    """Format a server-returned ACL for printing."""
    return bq_client_utils.FormatAcl(acl)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatSchema(schema):
    """Format a schema for printing."""
    return bq_client_utils.FormatSchema(schema)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def NormalizeWait(wait):
    return bq_client_utils.NormalizeWait(wait)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def ValidatePrintFormat(print_format):
    return bq_client_utils.ValidatePrintFormat(print_format)

  # TODO(b/324243535): Delete these once the migration is complete.
  # pylint: disable=protected-access
  @staticmethod
  def _ParseDatasetIdentifier(identifier):
    return bq_client_utils._ParseDatasetIdentifier(identifier)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def _ShiftInformationSchema(dataset_id, table_id):
    """Moves "INFORMATION_SCHEMA" to table_id for dataset qualified tables."""
    return bq_client_utils._ShiftInformationSchema(dataset_id, table_id)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def _ParseIdentifier(identifier):
    """Parses identifier into a tuple of (possibly empty) identifiers.

    This will parse the identifier into a tuple of the form
    (project_id, dataset_id, table_id) without doing any validation on
    the resulting names; missing names are returned as ''. The
    interpretation of these identifiers depends on the context of the
    caller. For example, if you know the identifier must be a job_id,
    then you can assume dataset_id is the job_id.

    Args:
      identifier: string, identifier to parse

    Returns:
      project_id, dataset_id, table_id: (string, string, string)
    """
    return bq_client_utils._ParseIdentifier(identifier)

  # pylint: enable=protected-access

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetProjectReference(self, identifier=''):
    """Determine a project reference from an identifier and self."""
    return bq_client_utils.GetProjectReference(
        id_fallbacks=self, identifier=identifier
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetDatasetReference(self, identifier=''):
    """Determine a DatasetReference from an identifier and self."""
    return bq_client_utils.GetDatasetReference(
        id_fallbacks=self, identifier=identifier
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetTableReference(self, identifier='', default_dataset_id=''):
    """Determine a TableReference from an identifier and self."""
    return bq_client_utils.GetTableReference(
        id_fallbacks=self,
        identifier=identifier,
        default_dataset_id=default_dataset_id,
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetModelReference(self, identifier=''):
    """Returns a ModelReference from an identifier."""
    return bq_client_utils.GetModelReference(
        id_fallbacks=self, identifier=identifier
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetRoutineReference(self, identifier=''):
    """Returns a RoutineReference from an identifier."""
    return bq_client_utils.GetRoutineReference(
        id_fallbacks=self, identifier=identifier
    )

  # TODO(b/324243535): Delete these once the migration is complete.
  def GetQueryDefaultDataset(self, identifier):
    return bq_client_utils.GetQueryDefaultDataset(identifier)

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetReference(self, identifier=''):
    """Try to deduce a project/dataset/table reference from a string.

    If the identifier is not compound, treat it as the most specific
    identifier we don't have as a flag, or as the table_id. If it is
    compound, fill in any unspecified part.

    Args:
      identifier: string, Identifier to create a reference for.

    Returns:
      A valid ProjectReference, DatasetReference, or TableReference.

    Raises:
      bq_error.BigqueryError: if no valid reference can be determined.
    """
    return bq_client_utils.GetReference(
        id_fallbacks=self, identifier=identifier
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetJobReference(self, identifier='', default_location=None):
    """Determine a JobReference from an identifier, location, and self."""
    return bq_client_utils.GetJobReference(
        id_fallbacks=self,
        identifier=identifier,
        default_location=default_location,
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetCapacityCommitmentReference(
      self,
      identifier=None,
      path=None,
      default_location=None,
      default_capacity_commitment_id=None,
      allow_commas=None,
  ):
    """Determine a CapacityCommitmentReference from an identifier and location."""
    return bq_client_utils.GetCapacityCommitmentReference(
        id_fallbacks=self,
        identifier=identifier,
        path=path,
        default_location=default_location,
        default_capacity_commitment_id=default_capacity_commitment_id,
        allow_commas=allow_commas,
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetConnectionReference(
      self,
      identifier=None,
      path=None,
      default_location=None,
      default_connection_id=None,
  ):
    """Determine a ConnectionReference from an identifier and location."""
    return bq_client_utils.GetConnectionReference(
        id_fallbacks=self,
        identifier=identifier,
        path=path,
        default_location=default_location,
        default_connection_id=default_connection_id,
    )

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

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def ConfigureFormatter(
      formatter, reference_type, print_format='list', object_info=None
  ):
    """Configure a formatter for a given reference type.

    If print_format is 'show', configures the formatter with several
    additional fields (useful for printing a single record).

    Arguments:
      formatter: TableFormatter object to configure.
      reference_type: Type of object this formatter will be used with.
      print_format: Either 'show' or 'list' to control what fields are included.

    Raises:
      ValueError: If reference_type or format is unknown.
    """
    return bq_client_utils.ConfigureFormatter(
        formatter, reference_type, print_format, object_info
    )

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def RaiseError(result):
    """Raises an appropriate BigQuery error given the json error result."""
    return bq_client_utils.RaiseError(result)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def IsFailedJob(job):
    """Predicate to determine whether or not a job failed."""
    return bq_client_utils.IsFailedJob(job)

  # TODO(b/324243535): Delete this once the migration is complete.
  @staticmethod
  def GetSessionId(job):
    """Helper to return the session id if the job is part of one.

    Args:
      job: a job resource to get statistics and sessionInfo from.

    Returns:
      sessionId, if the job is part of a session.
    """
    return bq_processor_utils.GetSessionId(job)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def RaiseIfJobError(job):
    """Raises a BigQueryError if the job is in an error state.

    Args:
      job: a Job resource.

    Returns:
      job, if it is not in an error state.

    Raises:
      bq_error.BigqueryError: A bq_error.BigqueryError instance
        based on the job's error description.
    """
    return bq_client_utils.RaiseIfJobError(job)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def GetJobTypeName(job_info):
    """Helper for job printing code."""
    return bq_client_utils.GetJobTypeName(job_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def ProcessSources(source_string):
    """Take a source string and return a list of URIs.

    The list will consist of either a single local filename, which
    we check exists and is a file, or a list of gs:// uris.

    Args:
      source_string: A comma-separated list of URIs.

    Returns:
      List of one or more valid URIs, as strings.

    Raises:
      bq_error.BigqueryClientError: if no valid list of sources can be
        determined.
    """
    return bq_client_utils.ProcessSources(source_string)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def ReadSchema(schema):
    """Create a schema from a string or a filename.

    If schema does not contain ':' and is the name of an existing
    file, read it as a JSON schema. If not, it must be a
    comma-separated list of fields in the form name:type.

    Args:
      schema: A filename or schema.

    Returns:
      The new schema (as a dict).

    Raises:
      bq_error.BigquerySchemaError: If the schema is invalid or the
        filename does not exist.
    """
    return bq_client_utils.ReadSchema(schema)

  # TODO(b/324243535): Delete this once the migration is complete.
  @staticmethod
  def _KindToName(kind):
    """Convert a kind to just a type name."""
    bq_processor_utils.KindToName(kind)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatInfoByType(object_info, object_type):
    """Format a single object_info (based on its 'kind' attribute)."""
    return bq_client_utils.FormatInfoByType(object_info, object_type)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatJobInfo(job_info):
    """Prepare a job_info for printing.

    Arguments:
      job_info: Job dict to format.

    Returns:
      The new job_info.
    """
    return bq_client_utils.FormatJobInfo(job_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatProjectInfo(project_info):
    """Prepare a project_info for printing.

    Arguments:
      project_info: Project dict to format.

    Returns:
      The new project_info.
    """
    return bq_client_utils.FormatProjectInfo(project_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatModelInfo(model_info):
    """Prepare a model for printing.

    Arguments:
      model_info: Model dict to format.

    Returns:
      A dictionary of model properties.
    """
    return bq_client_utils.FormatModelInfo(model_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatRoutineDataType(data_type):
    """Converts a routine data type to a pretty string representation.

    Arguments:
      data_type: Routine data type dict to format.

    Returns:
      A formatted string.
    """
    return bq_client_utils.FormatRoutineDataType(data_type)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatRoutineTableType(table_type):
    """Converts a routine table type to a pretty string representation.

    Arguments:
      table_type: Routine table type dict to format.

    Returns:
      A formatted string.
    """
    return bq_client_utils.FormatRoutineTableType(table_type)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatRoutineArgumentInfo(routine_type, argument):
    """Converts a routine argument to a pretty string representation.

    Arguments:
      routine_type: The routine type of the corresponding routine. It's of
        string type corresponding to the string value of enum
        cloud.bigquery.v2.Routine.RoutineType.
      argument: Routine argument dict to format.

    Returns:
      A formatted string.
    """
    return bq_client_utils.FormatRoutineArgumentInfo(routine_type, argument)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatRoutineInfo(routine_info):
    """Prepare a routine for printing.

    Arguments:
      routine_info: Routine dict to format.

    Returns:
      A dictionary of routine properties.
    """
    return bq_client_utils.FormatRoutineInfo(routine_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatRowAccessPolicyInfo(row_access_policy_info):
    """Prepare a row access policy for printing.

    Arguments:
      row_access_policy_info: Row access policy dict to format.

    Returns:
      A dictionary of row access policy properties.
    """
    return bq_client_utils.FormatRowAccessPolicyInfo(row_access_policy_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatDatasetInfo(dataset_info):
    """Prepare a dataset_info for printing.

    Arguments:
      dataset_info: Dataset dict to format.

    Returns:
      The new dataset_info.
    """
    return bq_client_utils.FormatDatasetInfo(dataset_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTableInfo(table_info):
    """Prepare a table_info for printing.

    Arguments:
      table_info: Table dict to format.

    Returns:
      The new table_info.
    """
    return bq_client_utils.FormatTableInfo(table_info)

  # TODO(b/324243535): Delete these once the migration is complete.

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTransferConfigInfo(transfer_config_info):
    """Prepare transfer config info for printing.

    Arguments:
      transfer_config_info: transfer config info to format.

    Returns:
      The new transfer config info.
    """
    return bq_client_utils.FormatTransferConfigInfo(transfer_config_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTrasferLogInfo(transfer_log_info):
    """Prepare transfer log info for printing.

    Arguments:
      transfer_log_info: transfer log info to format.

    Returns:
      The new transfer config log.
    """
    return bq_client_utils.FormatTransferLogInfo(transfer_log_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTransferRunInfo(transfer_run_info):
    """Prepare transfer run info for printing.

    Arguments:
      transfer_run_info: transfer run info to format.

    Returns:
      The new transfer run info.
    """
    return bq_client_utils.FormatTransferRunInfo(transfer_run_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatReservationInfo(reservation, reference_type):
    """Prepare a reservation for printing.

    Arguments:
      reservation: reservation to format.
      reference_type: Type of reservation.

    Returns:
      A dictionary of reservation properties.
    """
    return bq_client_utils.FormatReservationInfo(reservation, reference_type)

  # TODO(b/324243535): Delete these once the migration is complete.
  @classmethod
  def FormatCapacityCommitmentInfo(cls, capacity_commitment):
    """Prepare a capacity commitment for printing.

    Arguments:
      capacity_commitment: capacity commitment to format.

    Returns:
      A dictionary of capacity commitment properties.
    """
    return bq_client_utils.FormatCapacityCommitmentInfo(capacity_commitment)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatReservationAssignmentInfo(reservation_assignment):
    """Prepare a reservation_assignment for printing.

    Arguments:
      reservation_assignment: reservation_assignment to format.

    Returns:
      A dictionary of reservation_assignment properties.
    """
    return bq_client_utils.FormatReservationAssignmentInfo(
        reservation_assignment
    )

  # TODO(b/324243535): Delete this once the migration is complete.
  @staticmethod
  def GetConnectionType(connection):
    return bq_processor_utils.GetConnectionType(connection)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatConnectionInfo(connection):
    """Prepare a connection object for printing.

    Arguments:
      connection: connection to format.

    Returns:
      A dictionary of connection properties.
    """
    return bq_client_utils.FormatConnectionInfo(connection)

  # TODO(b/324243535): Delete this once the migration is complete.
  @staticmethod
  def ConstructObjectReference(object_info):
    """Construct a Reference from a server response."""
    return bq_processor_utils.ConstructObjectReference(object_info)

  # TODO(b/324243535): Delete this once the migration is complete.
  @staticmethod
  def ConstructObjectInfo(reference):
    """Construct an Object from an ObjectReference."""
    return bq_processor_utils.ConstructObjectInfo(reference)

  # TODO(b/324243535): Delete this once the migration is complete.
  def _PrepareListRequest(
      self, reference, max_results=None, page_token=None, filter_expression=None
  ):
    """Create and populate a list request."""
    return bq_processor_utils.PrepareListRequest(
        reference, max_results, page_token, filter_expression
    )

  # TODO(b/324243535): Delete these once the migration is complete.

  # TODO(b/324243535): Delete this once the migration is complete.
  def _PrepareTransferListRequest(
      self,
      reference,
      location,
      page_size=None,
      page_token=None,
      data_source_ids=None,
  ):
    """Create and populate a list request."""
    return bq_processor_utils.PrepareTransferListRequest(
        reference, location, page_size, page_token, data_source_ids
    )

  # TODO(b/324243535): Delete this once the migration is complete.
  def _PrepareTransferRunListRequest(
      self,
      reference,
      run_attempt,
      max_results=None,
      page_token=None,
      states=None,
  ):
    """Create and populate a transfer run list request."""
    return bq_processor_utils.PrepareTransferRunListRequest(
        reference, run_attempt, max_results, page_token, states
    )

  # TODO(b/324243535): Delete this once the migration is complete.
  def _PrepareListTransferLogRequest(
      self, reference, max_results=None, page_token=None, message_type=None
  ):
    """Create and populate a transfer log list request."""
    return bq_processor_utils.PrepareListTransferLogRequest(
        reference, max_results, page_token, message_type
    )

  # TODO(b/324243535): Delete these once the migration is complete.
  def _NormalizeProjectReference(self, reference):
    return bq_client_utils.NormalizeProjectReference(self, reference)

  def ListJobRefs(self, **kwds):
    return list(
        map(  # pylint: disable=g-long-lambda
            bq_processor_utils.ConstructObjectReference, self.ListJobs(**kwds)
        )
    )

  def ListJobs(
      self,
      reference=None,
      max_results=None,
      page_token=None,
      state_filter=None,
      min_creation_time=None,
      max_creation_time=None,
      all_users=None,
      parent_job_id=None,
  ):
    # pylint: disable=g-doc-args
    """Return a list of jobs.

    Args:
      reference: The ProjectReference to list jobs for.
      max_results: The maximum number of jobs to return.
      page_token: Current page token (optional).
      state_filter: A single state filter or a list of filters to apply. If not
        specified, no filtering is applied.
      min_creation_time: Timestamp in milliseconds. Only return jobs created
        after or at this timestamp.
      max_creation_time: Timestamp in milliseconds. Only return jobs created
        before or at this timestamp.
      all_users: Whether to list jobs for all users of the project. Requesting
        user must be an owner of the project to list all jobs.
      parent_job_id: Retrieve only child jobs belonging to this parent; None to
        retrieve top-level jobs.

    Returns:
      A list of jobs.
    """
    return self.ListJobsWithTokenAndUnreachable(
        reference,
        max_results,
        page_token,
        state_filter,
        min_creation_time,
        max_creation_time,
        all_users,
        parent_job_id,
    )['results']

  def ListJobsWithTokenAndUnreachable(
      self,
      reference=None,
      max_results=None,
      page_token=None,
      state_filter=None,
      min_creation_time=None,
      max_creation_time=None,
      all_users=None,
      parent_job_id=None,
  ):
    # pylint: disable=g-doc-args
    """Return a list of jobs.

    Args:
      reference: The ProjectReference to list jobs for.
      max_results: The maximum number of jobs to return.
      page_token: Current page token (optional).
      state_filter: A single state filter or a list of filters to apply. If not
        specified, no filtering is applied.
      min_creation_time: Timestamp in milliseconds. Only return jobs created
        after or at this timestamp.
      max_creation_time: Timestamp in milliseconds. Only return jobs created
        before or at this timestamp.
      all_users: Whether to list jobs for all users of the project. Requesting
        user must be an owner of the project to list all jobs.
      parent_job_id: Retrieve only child jobs belonging to this parent; None to
        retrieve top-level jobs.

    Returns:
      A dict that contains enytries:
        'results': a list of jobs
        'token': nextPageToken for the last page, if present.
    """
    reference = bq_client_utils.NormalizeProjectReference(
        id_fallbacks=self, reference=reference
    )
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ProjectReference,
        method='ListJobs',
    )
    if max_results is not None:
      if max_results > bq_processor_utils.MAX_RESULTS:
        max_results = bq_processor_utils.MAX_RESULTS
    request = bq_processor_utils.PrepareListRequest(
        reference, max_results, page_token
    )
    if state_filter is not None:
      # The apiclient wants enum values as lowercase strings.
      if isinstance(state_filter, str):
        state_filter = state_filter.lower()
      else:
        state_filter = [s.lower() for s in state_filter]
    bq_processor_utils.ApplyParameters(
        request,
        projection='full',
        state_filter=state_filter,
        all_users=all_users,
        parent_job_id=parent_job_id,
    )
    if min_creation_time is not None:
      request['minCreationTime'] = min_creation_time
    if max_creation_time is not None:
      request['maxCreationTime'] = max_creation_time
    result = self.apiclient.jobs().list(**request).execute()
    results = result.get('jobs', [])
    if max_results is not None:
      while 'nextPageToken' in result and len(results) < max_results:
        request['maxResults'] = max_results - len(results)
        request['pageToken'] = result['nextPageToken']
        result = self.apiclient.jobs().list(**request).execute()
        results.extend(result.get('jobs', []))
    response = dict(results=results)
    if 'nextPageToken' in result:
      response['token'] = result['nextPageToken']
    # The 'unreachable' field is a list of skipped locations that were
    # unreachable. The field definition is
    # google3/google/cloud/bigquery/v2/job.proto;rcl=622304818;l=593
    if 'unreachable' in result:
      response['unreachable'] = result['unreachable']
    return response

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
            self.ListDatasets(**kwds),
        )
    )

  # TODO(b/324243535): Delete these once the migration is complete.
  def ListDatasets(
      self,
      reference=None,
      max_results=None,
      page_token=None,
      list_all=None,
      filter_expression=None,
  ):
    """List the datasets associated with this reference."""
    return client_dataset.ListDatasets(
        apiclient=self.apiclient,
        id_fallbacks=self,
        reference=reference,
        max_results=max_results,
        page_token=page_token,
        list_all=list_all,
        filter_expression=filter_expression,
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

  def _ListRowAccessPolicies(
      self,
      table_reference: 'bq_id_utils.ApiClientHelper.TableReference',
      page_size: int,
      page_token: str,
  ) -> Dict[str, List[Any]]:
    """Lists row access policies for the given table reference."""
    return (
        self.GetRowAccessPoliciesApiClient()
        .rowAccessPolicies()
        .list(
            projectId=table_reference.projectId,
            datasetId=table_reference.datasetId,
            tableId=table_reference.tableId,
            pageSize=page_size,
            pageToken=page_token,
        )
        .execute()
    )

  def ListRowAccessPoliciesWithGrantees(
      self,
      table_reference: 'bq_id_utils.ApiClientHelper.TableReference',
      page_size: int,
      page_token: str,
      max_concurrent_iam_calls: int = 1,
  ) -> Dict[str, List[Any]]:
    """Lists row access policies for the given table reference.

    Arguments:
      table_reference: Reference to the table.
      page_size: Number of results to return.
      page_token: Token to retrieve the next page of results.
      max_concurrent_iam_calls: Number of concurrent calls to getIAMPolicy.

    Returns:
      A dict that contains entries:
        'rowAccessPolicies': a list of row access policies, with an additional
          'grantees' field that contains the row access policy grantees.
        'nextPageToken': nextPageToken for the next page, if present.
    """
    response = self._ListRowAccessPolicies(
        table_reference, page_size, page_token
    )
    if 'rowAccessPolicies' in response:
      row_access_policies = response['rowAccessPolicies']
      parallel.RunInParallel(
          function=self._SetRowAccessPolicyGrantees,
          list_of_kwargs_to_function=[
              {'row_access_policy': row_access_policy}
              for row_access_policy in row_access_policies
          ],
          num_workers=max_concurrent_iam_calls,
          cancel_futures=True,
      )
    return response

  def _SetRowAccessPolicyGrantees(self, row_access_policy):
    """Sets the grantees on the given Row Access Policy."""
    row_access_policy_ref = (
        bq_id_utils.ApiClientHelper.RowAccessPolicyReference.Create(
            **row_access_policy['rowAccessPolicyReference']
        )
    )
    iam_policy = self.GetRowAccessPolicyIAMPolicy(row_access_policy_ref)
    grantees = self._GetGranteesFromRowAccessPolicyIamPolicy(iam_policy)
    row_access_policy['grantees'] = grantees

  def _GetGranteesFromRowAccessPolicyIamPolicy(self, iam_policy):
    """Returns the filtered data viewer members of the given IAM policy."""
    bindings = iam_policy.get('bindings')
    if not bindings:
      return []

    filtered_data_viewer_binding = next(
        (
            binding
            for binding in bindings
            if binding.get('role') == _FILTERED_DATA_VIEWER_ROLE
        ),
        None,
    )
    if not filtered_data_viewer_binding:
      return []

    return filtered_data_viewer_binding.get('members', [])

  # TODO(b/324243535): Delete these once the migration is complete.
  def GetDatasetIAMPolicy(self, reference):
    """Gets IAM policy for the given dataset resource.

    Arguments:
      reference: the DatasetReference for the dataset resource.

    Returns:
      The IAM policy attached to the given dataset resource.

    Raises:
      TypeError: if reference is not a DatasetReference.
    """
    return client_dataset.GetDatasetIAMPolicy(
        apiclient=self.GetIAMPolicyApiClient(), reference=reference
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

  def GetRowAccessPolicyIAMPolicy(
      self, reference: 'bq_id_utils.ApiClientHelper.RowAccessPolicyReference'
  ) -> Policy:
    """Gets IAM policy for the given row access policy resource.

    Arguments:
      reference: the RowAccessPolicyReference for the row access policy
        resource.

    Returns:
      The IAM policy attached to the given row access policy resource.

    Raises:
      TypeError: if reference is not a RowAccessPolicyReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.RowAccessPolicyReference,
        method='GetRowAccessPolicyIAMPolicy',
    )
    formatted_resource = (
        'projects/%s/datasets/%s/tables/%s/rowAccessPolicies/%s'
        % (
            reference.projectId,
            reference.datasetId,
            reference.tableId,
            reference.policyId,
        )
    )
    return (
        self.GetIAMPolicyApiClient()
        .rowAccessPolicies()
        .getIamPolicy(resource=formatted_resource)
        .execute()
    )

  # TODO(b/324243535): Delete these once the migration is complete.
  def SetDatasetIAMPolicy(self, reference, policy):
    """Sets IAM policy for the given dataset resource.

    Arguments:
      reference: the DatasetReference for the dataset resource.
      policy: The policy string in JSON format.

    Returns:
      The updated IAM policy attached to the given dataset resource.

    Raises:
      TypeError: if reference is not a DatasetReference.
    """
    return client_dataset.SetDatasetIAMPolicy(
        apiclient=self.GetIAMPolicyApiClient(),
        reference=reference,
        policy=policy,
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

  def CopyTable(
      self,
      source_references,
      dest_reference,
      create_disposition=None,
      write_disposition=None,
      ignore_already_exists=False,
      encryption_configuration=None,
      operation_type='COPY',
      destination_expiration_time=None,
      **kwds,
  ):
    """Copies a table.

    Args:
      source_references: TableReferences of source tables.
      dest_reference: TableReference of destination table.
      create_disposition: Optional. Specifies the create_disposition for the
        dest_reference.
      write_disposition: Optional. Specifies the write_disposition for the
        dest_reference.
      ignore_already_exists: Whether to ignore "already exists" errors.
      encryption_configuration: Optional. Allows user to encrypt the table from
        the copy table command with Cloud KMS key. Passed as a dictionary in the
        following format: {'kmsKeyName': 'destination_kms_key'}
      **kwds: Passed on to ExecuteJob.

    Returns:
      The job description, or None for ignored errors.

    Raises:
      BigqueryDuplicateError: when write_disposition 'WRITE_EMPTY' is
        specified and the dest_reference table already exists.
    """
    for src_ref in source_references:
      bq_id_utils.typecheck(
          src_ref,
          bq_id_utils.ApiClientHelper.TableReference,
          method='CopyTable',
      )
    bq_id_utils.typecheck(
        dest_reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='CopyTable',
    )
    copy_config = {
        'destinationTable': dict(dest_reference),
        'sourceTables': [dict(src_ref) for src_ref in source_references],
    }
    if encryption_configuration:
      copy_config['destinationEncryptionConfiguration'] = (
          encryption_configuration
      )

    if operation_type:
      copy_config['operationType'] = operation_type

    if destination_expiration_time:
      copy_config['destinationExpirationTime'] = destination_expiration_time

    bq_processor_utils.ApplyParameters(
        copy_config,
        create_disposition=create_disposition,
        write_disposition=write_disposition,
    )

    try:
      return self.ExecuteJob({'copy': copy_config}, **kwds)
    except bq_error.BigqueryDuplicateError as e:
      if ignore_already_exists:
        return None
      raise e

  # TODO(b/324243535): Delete these once the migration is complete.
  def DatasetExists(
      self, reference: 'bq_id_utils.ApiClientHelper.DatasetReference'
  ) -> bool:
    """Returns true if a dataset exists."""
    return client_dataset.DatasetExists(
        apiclient=self.apiclient, reference=reference
    )

  # TODO(b/324243535): Delete these once the migration is complete.
  def GetDatasetRegion(
      self, reference: 'bq_id_utils.ApiClientHelper.DatasetReference'
  ) -> Optional[str]:
    """Returns the region of a dataset as a string."""
    return client_dataset.GetDatasetRegion(
        apiclient=self.apiclient, reference=reference
    )

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

  def JobExists(
      self, reference: 'bq_id_utils.ApiClientHelper.JobReference'
  ) -> bool:
    """Returns true if the job exists."""
    bq_id_utils.typecheck(
        reference, bq_id_utils.ApiClientHelper.JobReference, method='JobExists'
    )
    try:
      return self.apiclient.jobs().get(**dict(reference)).execute()
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

  # TODO(b/324243535): Delete these once the migration is complete.
  def CreateDataset(
      self,
      reference,
      ignore_existing=False,
      description=None,
      display_name=None,
      acl=None,
      default_table_expiration_ms=None,
      default_partition_expiration_ms=None,
      data_location=None,
      labels=None,
      default_kms_key=None,
      source_dataset_reference=None,
      external_source=None,
      connection_id=None,
      max_time_travel_hours=None,
      storage_billing_model=None,
      resource_tags=None,
  ):
    """Create a dataset corresponding to DatasetReference.

    Args:
      reference: the DatasetReference to create.
      ignore_existing: (boolean, default False) If False, raise an exception if
        the dataset already exists.
      description: an optional dataset description.
      display_name: an optional friendly name for the dataset.
      acl: an optional ACL for the dataset, as a list of dicts.
      default_table_expiration_ms: Default expiration time to apply to new
        tables in this dataset.
      default_partition_expiration_ms: Default partition expiration time to
        apply to new partitioned tables in this dataset.
      data_location: Location where the data in this dataset should be stored.
        Must be either 'EU' or 'US'. If specified, the project that owns the
        dataset must be enabled for data location.
      labels: An optional dict of labels.
      default_kms_key: An optional kms dey that will apply to all newly created
        tables in the dataset, if no explicit key is supplied in the creating
        request.
      source_dataset_reference: An optional ApiClientHelper.DatasetReference
        that will be the source of this linked dataset. #
      external_source: External source that backs this dataset.
      connection_id: Connection used for accessing the external_source.
      max_time_travel_hours: Optional. Define the max time travel in hours. The
        value can be from 48 to 168 hours (2 to 7 days). The default value is
        168 hours if this is not set.
      storage_billing_model: Optional. Sets the storage billing model for the
        dataset.
      resource_tags: an optional dict of tags to attach to the dataset.

    Raises:
      TypeError: if reference is not an ApiClientHelper.DatasetReference
        or if source_dataset_reference is provided but is not an
        bq_id_utils.ApiClientHelper.DatasetReference.
        or if both external_dataset_reference and source_dataset_reference
        are provided or if not all required arguments for external database is
        provided.
      BigqueryDuplicateError: if reference exists and ignore_existing
         is False.
    """
    return client_dataset.CreateDataset(
        apiclient=self.apiclient,
        reference=reference,
        ignore_existing=ignore_existing,
        description=description,
        display_name=display_name,
        acl=acl,
        default_table_expiration_ms=default_table_expiration_ms,
        default_partition_expiration_ms=default_partition_expiration_ms,
        data_location=data_location,
        labels=labels,
        default_kms_key=default_kms_key,
        source_dataset_reference=source_dataset_reference,
        external_source=external_source,
        connection_id=connection_id,
        max_time_travel_hours=max_time_travel_hours,
        storage_billing_model=storage_billing_model,
        resource_tags=resource_tags,
    )

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

  # TODO(b/324243535): Delete this once the migration is complete.
  def ProcessParamsFlag(self, params, items):
    """Processes the params flag.

    Args:
      params: The user specified parameters. The parameters should be in JSON
        format given as a string. Ex: --params="{'param':'value'}".
      items: The body that contains information of all the flags set.

    Returns:
      items: The body after it has been updated with the params flag.

    Raises:
      bq_error.BigqueryError: If there is an error with the given params.
    """
    return bq_processor_utils.ProcessParamsFlag(params, items)

  # TODO(b/324243535): Delete this once the migration is complete.
  def ProcessRefreshWindowDaysFlag(
      self, refresh_window_days, data_source_info, items, data_source
  ):
    """Processes the Refresh Window Days flag.

    Args:
      refresh_window_days: The user specified refresh window days.
      data_source_info: The data source of the transfer config.
      items: The body that contains information of all the flags set.
      data_source: The data source of the transfer config.

    Returns:
      items: The body after it has been updated with the
      refresh window days flag.
    Raises:
      bq_error.BigqueryError: If the data source does not support (custom)
        window days.
    """
    return bq_processor_utils.ProcessRefreshWindowDaysFlag(
        refresh_window_days, data_source_info, items, data_source
    )

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

  # TODO(b/324243535): Delete these once the migration is complete.
  def UpdateDataset(
      self,
      reference: bq_id_utils.ApiClientHelper.DatasetReference,
      description: Optional[str] = None,
      display_name: Optional[str] = None,
      acl=None,
      default_table_expiration_ms=None,
      default_partition_expiration_ms=None,
      labels_to_set=None,
      label_keys_to_remove=None,
      etag=None,
      default_kms_key=None,
      max_time_travel_hours=None,
      storage_billing_model=None,
      tags_to_attach: Optional[Dict[str, str]] = None,
      tags_to_remove: Optional[List[str]] = None,
      clear_all_tags: Optional[bool] = False,
  ):
    """Updates a dataset.

    Args:
      reference: the DatasetReference to update.
      description: an optional dataset description.
      display_name: an optional friendly name for the dataset.
      acl: an optional ACL for the dataset, as a list of dicts.
      default_table_expiration_ms: optional number of milliseconds for the
        default expiration duration for new tables created in this dataset.
      default_partition_expiration_ms: optional number of milliseconds for the
        default partition expiration duration for new partitioned tables created
        in this dataset.
      labels_to_set: an optional dict of labels to set on this dataset.
      label_keys_to_remove: an optional list of label keys to remove from this
        dataset.
      etag: if set, checks that etag in the existing dataset matches.
      default_kms_key: An optional kms dey that will apply to all newly created
        tables in the dataset, if no explicit key is supplied in the creating
        request.
      max_time_travel_hours: Optional. Define the max time travel in hours. The
        value can be from 48 to 168 hours (2 to 7 days). The default value is
        168 hours if this is not set.
      storage_billing_model: Optional. Sets the storage billing model for the
        dataset.
      tags_to_attach: an optional dict of tags to attach to the dataset
      tags_to_remove: an optional list of tag keys to remove from the dataset
      clear_all_tags: if set, clears all the tags attached to the dataset

    Raises:
      TypeError: if reference is not a DatasetReference.
    """
    return client_dataset.UpdateDataset(
        apiclient=self.apiclient,
        reference=reference,
        description=description,
        display_name=display_name,
        acl=acl,
        default_table_expiration_ms=default_table_expiration_ms,
        default_partition_expiration_ms=default_partition_expiration_ms,
        labels_to_set=labels_to_set,
        label_keys_to_remove=label_keys_to_remove,
        etag=etag,
        default_kms_key=default_kms_key,
        max_time_travel_hours=max_time_travel_hours,
        storage_billing_model=storage_billing_model,
        tags_to_attach=tags_to_attach,
        tags_to_remove=tags_to_remove,
        clear_all_tags=clear_all_tags,
    )

  # TODO(b/324243535): Delete these once the migration is complete.
  def _ExecuteGetDatasetRequest(self, reference, etag: Optional[str] = None):
    """Executes request to get dataset.

    Args:
      reference: the DatasetReference to get.
      etag: if set, checks that etag in the existing dataset matches.

    Returns:
    The result of executing the request, if it succeeds.
    """
    # pylint: disable=protected-access
    return client_dataset._ExecuteGetDatasetRequest(
        apiclient=self.apiclient, reference=reference, etag=etag
    )
    # pylint: enable=protected-access

  # TODO(b/324243535): Delete these once the migration is complete.
  def _ExecutePatchDatasetRequest(
      self, reference, dataset, etag: Optional[str] = None
  ):
    """Executes request to patch dataset.

    Args:
      reference: the DatasetReference to patch.
      dataset: the body of request
      etag: if set, checks that etag in the existing dataset matches.
    """
    # pylint: disable=protected-access
    return client_dataset._ExecutePatchDatasetRequest(
        apiclient=self.apiclient,
        reference=reference,
        dataset=dataset,
        etag=etag,
    )
    # pylint: enable=protected-access

  # TODO(b/324243535): Delete these once the migration is complete.
  def DeleteDataset(
      self, reference, ignore_not_found=False, delete_contents=None
  ):
    return client_dataset.DeleteDataset(
        apiclient=self.apiclient,
        reference=reference,
        ignore_not_found=ignore_not_found,
        delete_contents=delete_contents,
    )

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

  def DeleteJob(self, reference, ignore_not_found=False):
    """Deletes JobReference reference.

    Args:
      reference: the JobReference to delete.
      ignore_not_found: Whether to ignore "not found" errors.

    Raises:
      TypeError: if reference is not a JobReference.
      bq_error.BigqueryNotFoundError: if reference does not exist and
        ignore_not_found is False.
    """
    bq_id_utils.typecheck(
        reference, bq_id_utils.ApiClientHelper.JobReference, method='DeleteJob'
    )
    try:
      self.apiclient.jobs().delete(**dict(reference)).execute()
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

  #################################
  ## Job control
  #################################

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def _ExecuteInChunksWithProgress(request):
    """Run an apiclient request with a resumable upload, showing progress.

    Args:
      request: an apiclient request having a media_body that is a
        MediaFileUpload(resumable=True).

    Returns:
      The result of executing the request, if it succeeds.

    Raises:
      BigQueryError: on a non-retriable error or too many retriable errors.
    """
    return bq_client_utils.ExecuteInChunksWithProgress(request)

  def StartJob(
      self,
      configuration,
      project_id=None,
      upload_file=None,
      job_id=None,
      location=None,
  ):
    """Start a job with the given configuration.

    Args:
      configuration: The configuration for a job.
      project_id: The project_id to run the job under. If None, self.project_id
        is used.
      upload_file: A file to include as a media upload to this request. Only
        valid on job requests that expect a media upload file.
      job_id: A unique job_id to use for this job. If a JobIdGenerator, a job id
        will be generated from the job configuration. If None, a unique job_id
        will be created for this request.
      location: Optional. The geographic location where the job should run.

    Returns:
      The job resource returned from the insert job request. If there is an
      error, the jobReference field will still be filled out with the job
      reference used in the request.

    Raises:
      bq_error.BigqueryClientConfigurationError: if project_id and
        self.project_id are None.
    """
    project_id = project_id or self.project_id
    if not project_id:
      raise bq_error.BigqueryClientConfigurationError(
          'Cannot start a job without a project id.'
      )
    configuration = configuration.copy()
    if self.job_property:
      configuration['properties'] = dict(
          prop.partition('=')[0::2] for prop in self.job_property
      )
    job_request = {'configuration': configuration}

    # Use the default job id generator if no job id was supplied.
    job_id = job_id or self.job_id_generator

    if isinstance(job_id, bq_client_utils.JobIdGenerator):
      job_id = job_id.Generate(configuration)

    if job_id is not None:
      job_reference = {'jobId': job_id, 'projectId': project_id}
      job_request['jobReference'] = job_reference
      if location:
        job_reference['location'] = location
    media_upload = ''
    if upload_file:
      resumable = self.enable_resumable_uploads
      # There is a bug in apiclient http lib that make uploading resumable files
      # with 0 length broken.
      if os.stat(upload_file).st_size == 0:
        resumable = False
      media_upload = http_request.MediaFileUpload(
          filename=upload_file,
          mimetype='application/octet-stream',
          resumable=resumable,
      )
    request = self.apiclient.jobs().insert(
        body=job_request, media_body=media_upload, projectId=project_id
    )
    if upload_file and resumable:
      result = bq_client_utils.ExecuteInChunksWithProgress(request)
    else:
      result = request.execute()
    return result

  def _StartQueryRpc(
      self,
      query,
      dry_run=None,
      use_cache=None,
      preserve_nulls=None,
      request_id=None,
      maximum_bytes_billed=None,
      max_results=None,
      timeout_ms=None,
      min_completion_ratio=None,
      project_id=None,
      external_table_definitions_json=None,
      udf_resources=None,
      use_legacy_sql=None,
      location=None,
      connection_properties=None,
      create_session=None,
      query_parameters=None,
      positional_parameter_mode=None,
      **kwds,
  ):
    """Executes the given query using the rpc-style query api.

    Args:
      query: Query to execute.
      dry_run: Optional. Indicates whether the query will only be validated and
        return processing statistics instead of actually running.
      use_cache: Optional. Whether to use the query cache. Caching is
        best-effort only and you should not make assumptions about whether or
        how long a query result will be cached.
      preserve_nulls: Optional. Indicates whether to preserve nulls in input
        data. Temporary flag; will be removed in a future version.
      request_id: Optional. The idempotency token for jobs.query
      maximum_bytes_billed: Optional. Upper limit on the number of billed bytes.
      max_results: Maximum number of results to return.
      timeout_ms: Timeout, in milliseconds, for the call to query().
      min_completion_ratio: Optional. Specifies the minimum fraction of data
        that must be scanned before a query returns. This value should be
        between 0.0 and 1.0 inclusive.
      project_id: Project id to use.
      external_table_definitions_json: Json representation of external table
        definitions.
      udf_resources: Array of inline and external UDF code resources.
      use_legacy_sql: The choice of using Legacy SQL for the query is optional.
        If not specified, the server will automatically determine the dialect
        based on query information, such as dialect prefixes. If no prefixes are
        found, it will default to Legacy SQL.
      location: Optional. The geographic location where the job should run.
      connection_properties: Optional. Connection properties to use when running
        the query, presented as a list of key/value pairs. A key of "time_zone"
        indicates that the query will be run with the default timezone
        corresponding to the value.
      create_session: Optional. True to create a session for the query.
      query_parameters: parameter values for use_legacy_sql=False queries.
      positional_parameter_mode: If true, set the parameter mode to POSITIONAL
        instead of the default NAMED.
      **kwds: Extra keyword arguments passed directly to jobs.Query().

    Returns:
      The query response.

    Raises:
      bq_error.BigqueryClientConfigurationError: if project_id and
        self.project_id are None.
      bq_error.BigqueryError: if query execution fails.
    """
    project_id = project_id or self.project_id
    if not project_id:
      raise bq_error.BigqueryClientConfigurationError(
          'Cannot run a query without a project id.'
      )
    request = {'query': query}
    if external_table_definitions_json:
      request['tableDefinitions'] = external_table_definitions_json
    if udf_resources:
      request['userDefinedFunctionResources'] = udf_resources
    if self.dataset_id:
      request['defaultDataset'] = bq_client_utils.GetQueryDefaultDataset(
          self.dataset_id
      )

    # If the request id flag is set, generate a random one if it is not provided
    # explicitly.
    if request_id is None and flags.FLAGS.jobs_query_use_request_id:
      request_id = str(uuid.uuid4())

    bq_processor_utils.ApplyParameters(
        request,
        preserve_nulls=preserve_nulls,
        request_id=request_id,
        maximum_bytes_billed=maximum_bytes_billed,
        use_query_cache=use_cache,
        timeout_ms=timeout_ms,
        max_results=max_results,
        use_legacy_sql=use_legacy_sql,
        min_completion_ratio=min_completion_ratio,
        location=location,
        create_session=create_session,
        query_parameters=query_parameters,
        parameter_mode=None
        if positional_parameter_mode is None
        else ('POSITIONAL' if positional_parameter_mode else 'NAMED'),
    )
    bq_processor_utils.ApplyParameters(
        request, connection_properties=connection_properties
    )
    bq_processor_utils.ApplyParameters(request, dry_run=dry_run)
    logging.debug(
        'Calling self.apiclient.jobs().query(%s, %s, %s)',
        request,
        project_id,
        kwds,
    )
    return (
        self.apiclient.jobs()
        .query(body=request, projectId=project_id, **kwds)
        .execute()
    )

  def GetQueryResults(
      self,
      job_id=None,
      project_id=None,
      max_results=None,
      timeout_ms=None,
      location=None,
  ):
    """Waits for a query job to run and returns results if complete.

    By default, waits 10s for the provided job to complete and either returns
    the results or a response where jobComplete is set to false. The timeout can
    be increased but the call is not guaranteed to wait for the specified
    timeout.

    Args:
      job_id: The job id of the query job that we are waiting to complete.
      project_id: The project id of the query job.
      max_results: The maximum number of results.
      timeout_ms: The number of milliseconds to wait for the query to complete.
      location: Optional. The geographic location of the job.

    Returns:
      The getQueryResults() result.

    Raises:
      bq_error.BigqueryClientConfigurationError: if project_id and
        self.project_id are None.
    """
    project_id = project_id or self.project_id
    if not project_id:
      raise bq_error.BigqueryClientConfigurationError(
          'Cannot get query results without a project id.'
      )
    kwds = {}
    bq_processor_utils.ApplyParameters(
        kwds,
        job_id=job_id,
        project_id=project_id,
        timeout_ms=timeout_ms,
        max_results=max_results,
        location=location,
    )
    return self.apiclient.jobs().getQueryResults(**kwds).execute()

  def RunJobSynchronously(
      self,
      configuration,
      project_id=None,
      upload_file=None,
      job_id=None,
      location=None,
  ):
    """Starts a job and waits for it to complete.

    Args:
      configuration: The configuration for a job.
      project_id: The project_id to run the job under. If None, self.project_id
        is used.
      upload_file: A file to include as a media upload to this request. Only
        valid on job requests that expect a media upload file.
      job_id: A unique job_id to use for this job. If a JobIdGenerator, a job id
        will be generated from the job configuration. If None, a unique job_id
        will be created for this request.
      location: Optional. The geographic location where the job should run.

    Returns:
      job, if it did not fail.

    Raises:
      BigQueryError: if the job fails.
    """
    result = self.StartJob(
        configuration,
        project_id=project_id,
        upload_file=upload_file,
        job_id=job_id,
        location=location,
    )
    if result['status']['state'] != 'DONE':
      job_reference = bq_processor_utils.ConstructObjectReference(result)
      result = self.WaitJob(job_reference)
    return bq_client_utils.RaiseIfJobError(result)

  def ExecuteJob(
      self,
      configuration,
      sync=None,
      project_id=None,
      upload_file=None,
      job_id=None,
      location=None,
  ):
    """Execute a job, possibly waiting for results."""
    if sync is None:
      sync = self.sync

    if sync:
      job = self.RunJobSynchronously(
          configuration,
          project_id=project_id,
          upload_file=upload_file,
          job_id=job_id,
          location=location,
      )
    else:
      job = self.StartJob(
          configuration,
          project_id=project_id,
          upload_file=upload_file,
          job_id=job_id,
          location=location,
      )
      bq_client_utils.RaiseIfJobError(job)
    return job

  def CancelJob(self, project_id=None, job_id=None, location=None):
    """Attempt to cancel the specified job if it is running.

    Args:
      project_id: The project_id to the job is running under. If None,
        self.project_id is used.
      job_id: The job id for this job.
      location: Optional. The geographic location of the job.

    Returns:
      The job resource returned for the job for which cancel is being requested.

    Raises:
      bq_error.BigqueryClientConfigurationError: if project_id or job_id
        are None.
    """
    project_id = project_id or self.project_id
    if not project_id:
      raise bq_error.BigqueryClientConfigurationError(
          'Cannot cancel a job without a project id.'
      )
    if not job_id:
      raise bq_error.BigqueryClientConfigurationError(
          'Cannot cancel a job without a job id.'
      )

    job_reference = bq_id_utils.ApiClientHelper.JobReference.Create(
        projectId=project_id, jobId=job_id, location=location
    )
    result = (
        self.apiclient.jobs().cancel(**dict(job_reference)).execute()['job']
    )
    if result['status']['state'] != 'DONE' and self.sync:
      job_reference = bq_processor_utils.ConstructObjectReference(result)
      result = self.WaitJob(job_reference=job_reference)
    return result

  # TODO(b/324243535): Delete these once the migration is complete.
  # pylint: disable=invalid-name
  WaitPrinter = bq_client_utils.WaitPrinter
  WaitPrinterHelper = bq_client_utils.WaitPrinterHelper
  QuietWaitPrinter = bq_client_utils.QuietWaitPrinter
  VerboseWaitPrinter = bq_client_utils.VerboseWaitPrinter
  TransitionWaitPrinter = bq_client_utils.TransitionWaitPrinter
  # pylint: enable=invalid-name

  def WaitJob(
      self,
      job_reference,
      status='DONE',
      wait=sys.maxsize,
      wait_printer_factory: Optional[
          Callable[[], bq_client_utils.TransitionWaitPrinter]
      ] = None,
  ):
    """Poll for a job to run until it reaches the requested status.

    Arguments:
      job_reference: JobReference to poll.
      status: (optional, default 'DONE') Desired job status.
      wait: (optional, default maxint) Max wait time.
      wait_printer_factory: (optional, defaults to self.wait_printer_factory)
        Returns a subclass of WaitPrinter that will be called after each job
        poll.

    Returns:
      The job object returned by the final status call.

    Raises:
      StopIteration: If polling does not reach the desired state before
        timing out.
      ValueError: If given an invalid wait value.
    """
    bq_id_utils.typecheck(
        job_reference,
        bq_id_utils.ApiClientHelper.JobReference,
        method='WaitJob',
    )
    start_time = time.time()
    job = None
    if wait_printer_factory:
      printer = wait_printer_factory()
    else:
      printer = self.wait_printer_factory()

    # This is a first pass at wait logic: we ping at 1s intervals a few
    # times, then increase to max(3, max_wait), and then keep waiting
    # that long until we've run out of time.
    waits = itertools.chain(
       itertools.repeat(1, 8), range(2, 30, 3),
       itertools.repeat(30))
    current_wait = 0
    current_status = 'UNKNOWN'
    in_error_state = False
    while current_wait <= wait:
      try:
        done, job = self.PollJob(job_reference, status=status, wait=wait)
        current_status = job['status']['state']
        in_error_state = False
        if done:
          printer.Print(job_reference.jobId, current_wait, current_status)
          break
      except bq_error.BigqueryCommunicationError as e:
        # Communication errors while waiting on a job are okay.
        logging.warning('Transient error during job status check: %s', e)
      except bq_error.BigqueryBackendError as e:
        # Temporary server errors while waiting on a job are okay.
        logging.warning('Transient error during job status check: %s', e)
      except BigqueryServiceError as e:
        # Among this catch-all class, some kinds are permanent
        # errors, so we don't want to retry indefinitely, but if
        # the error is transient we'd like "wait" to get past it.
        if in_error_state: raise
        in_error_state = True

      # For every second we're polling, update the message to the user.
      for _ in range(next(waits)):
        current_wait = time.time() - start_time
        printer.Print(job_reference.jobId, current_wait, current_status)
        time.sleep(1)
    else:
      raise StopIteration(
          'Wait timed out. Operation not finished, in state %s'
          % (current_status,)
      )
    printer.Done()
    return job

  def PollJob(self, job_reference, status='DONE', wait=0):
    """Poll a job once for a specific status.

    Arguments:
      job_reference: JobReference to poll.
      status: (optional, default 'DONE') Desired job status.
      wait: (optional, default 0) Max server-side wait time for one poll call.

    Returns:
      Tuple (in_state, job) where in_state is True if job is
      in the desired state.

    Raises:
      ValueError: If given an invalid wait value.
    """
    bq_id_utils.typecheck(
        job_reference,
        bq_id_utils.ApiClientHelper.JobReference,
        method='PollJob',
    )
    wait = bq_client_utils.NormalizeWait(wait)
    job = self.apiclient.jobs().get(**dict(job_reference)).execute()
    current = job['status']['state']
    return (current == status, job)

  #################################
  ## Wrappers for job types
  #################################

  def RunQuery(self, start_row, max_rows, **kwds):
    """Run a query job synchronously, and return the result.

    Args:
      start_row: first row to read.
      max_rows: number of rows to read.
      **kwds: Passed on to self.Query.

    Returns:
      A tuple where the first item is the list of fields and the
      second item a list of rows.
    """
    new_kwds = dict(kwds)
    new_kwds['sync'] = True
    job = self.Query(**new_kwds)

    return self.ReadSchemaAndJobRows(
        job['jobReference'], start_row=start_row, max_rows=max_rows
    )

  def RunQueryRpc(
      self,
      query,
      dry_run=None,
      use_cache=None,
      preserve_nulls=None,
      request_id=None,
      maximum_bytes_billed=None,
      max_results=None,
      wait=sys.maxsize,
      min_completion_ratio=None,
      wait_printer_factory: Optional[Callable[[], WaitPrinter]] = None,
      max_single_wait=None,
      external_table_definitions_json=None,
      udf_resources=None,
      location=None,
      connection_properties=None,
      **kwds,
  ):
    """Executes the given query using the rpc-style query api.

    Args:
      query: Query to execute.
      dry_run: Optional. Indicates whether the query will only be validated and
        return processing statistics instead of actually running.
      use_cache: Optional. Whether to use the query cache. Caching is
        best-effort only and you should not make assumptions about whether or
        how long a query result will be cached.
      preserve_nulls: Optional. Indicates whether to preserve nulls in input
        data. Temporary flag; will be removed in a future version.
      request_id: Optional. Specifies the idempotency token for the request.
      maximum_bytes_billed: Optional. Upper limit on maximum bytes billed.
      max_results: Optional. Maximum number of results to return.
      wait: (optional, default maxint) Max wait time in seconds.
      min_completion_ratio: Optional. Specifies the minimum fraction of data
        that must be scanned before a query returns. This value should be
        between 0.0 and 1.0 inclusive.
      wait_printer_factory: (optional, defaults to self.wait_printer_factory)
        Returns a subclass of WaitPrinter that will be called after each job
        poll.
      max_single_wait: Optional. Maximum number of seconds to wait for each call
        to query() / getQueryResults().
      external_table_definitions_json: Json representation of external table
        definitions.
      udf_resources: Array of inline and remote UDF resources.
      location: Optional. The geographic location where the job should run.
      connection_properties: Optional. Connection properties to use when running
        the query, presented as a list of key/value pairs. A key of "time_zone"
        indicates that the query will be run with the default timezone
        corresponding to the value.
      **kwds: Passed directly to self.ExecuteSyncQuery.

    Raises:
      bq_error.BigqueryClientError: if no query is provided.
      StopIteration: if the query does not complete within wait seconds.
      bq_error.BigqueryError: if query fails.

    Returns:
      A tuple (schema fields, row results, execution metadata).
        For regular queries, the execution metadata dict contains
        the 'State' and 'status' elements that would be in a job result
        after FormatJobInfo().
        For dry run queries schema and rows are empty, the execution metadata
        dict contains statistics
    """
    if not self.sync:
      raise bq_error.BigqueryClientError(
          'Running RPC-style query asynchronously is not supported'
      )
    if not query:
      raise bq_error.BigqueryClientError('No query string provided')

    if request_id is not None and not flags.FLAGS.jobs_query_use_request_id:
      raise bq_error.BigqueryClientError('request_id is not yet supported')

    if wait_printer_factory:
      printer = wait_printer_factory()
    else:
      printer = self.wait_printer_factory()

    start_time = time.time()
    elapsed_time = 0
    job_reference = None
    current_wait_ms = None
    while True:
      try:
        elapsed_time = 0 if job_reference is None else time.time() - start_time
        remaining_time = wait - elapsed_time
        if max_single_wait is not None:
          # Compute the current wait, being careful about overflow, since
          # remaining_time may be counting down from sys.maxint.
          current_wait_ms = int(min(remaining_time, max_single_wait) * 1000)
          if current_wait_ms < 0:
            current_wait_ms = sys.maxsize
        if remaining_time < 0:
          raise StopIteration('Wait timed out. Query not finished.')
        if job_reference is None:
          # We haven't yet run a successful Query(), so we don't
          # have a job id to check on.
          rows_to_read = max_results
          if self.max_rows_per_request is not None:
            if rows_to_read is None:
              rows_to_read = self.max_rows_per_request
            else:
              rows_to_read = min(self.max_rows_per_request, int(rows_to_read))
          result = self._StartQueryRpc(
              query=query,
              preserve_nulls=preserve_nulls,
              request_id=request_id,
              maximum_bytes_billed=maximum_bytes_billed,
              use_cache=use_cache,
              dry_run=dry_run,
              min_completion_ratio=min_completion_ratio,
              timeout_ms=current_wait_ms,
              max_results=rows_to_read,
              external_table_definitions_json=external_table_definitions_json,
              udf_resources=udf_resources,
              location=location,
              connection_properties=connection_properties,
              **kwds,
          )
          if dry_run:
            execution = dict(
                statistics=dict(
                    query=dict(
                        totalBytesProcessed=result['totalBytesProcessed'],
                        cacheHit=result['cacheHit'],
                    )
                )
            )
            if 'schema' in result:
              execution['statistics']['query']['schema'] = result['schema']
            return ([], [], execution)
          if 'jobReference' in result:
            job_reference = bq_id_utils.ApiClientHelper.JobReference.Create(
                **result['jobReference']
            )
        else:
          # The query/getQueryResults methods do not return the job state,
          # so we just print 'RUNNING' while we are actively waiting.
          printer.Print(job_reference.jobId, elapsed_time, 'RUNNING')
          result = self.GetQueryResults(
              job_reference.jobId,
              max_results=max_results,
              timeout_ms=current_wait_ms,
              location=location,
          )
        if result['jobComplete']:
          (schema, rows) = self.ReadSchemaAndJobRows(
              dict(job_reference) if job_reference else {},
              start_row=0,
              max_rows=max_results,
              result_first_page=result,
          )
          # If we get here, we must have succeeded.  We could still have
          # non-fatal errors though.
          status = {}
          if 'errors' in result:
            status['errors'] = result['errors']
          execution = {
              'State': 'SUCCESS',
              'status': status,
              'jobReference': job_reference,
          }
          return (schema, rows, execution)
      except bq_error.BigqueryCommunicationError as e:
        # Communication errors while waiting on a job are okay.
        logging.warning('Transient error during query: %s', e)
      except bq_error.BigqueryBackendError as e:
        # Temporary server errors while waiting on a job are okay.
        logging.warning('Transient error during query: %s', e)

  def Query(
      self,
      query,
      destination_table=None,
      create_disposition=None,
      write_disposition=None,
      priority=None,
      preserve_nulls=None,
      allow_large_results=None,
      dry_run=None,
      use_cache=None,
      min_completion_ratio=None,
      flatten_results=None,
      external_table_definitions_json=None,
      udf_resources=None,
      maximum_billing_tier=None,
      maximum_bytes_billed=None,
      use_legacy_sql=None,
      schema_update_options=None,
      labels=None,
      query_parameters=None,
      time_partitioning=None,
      destination_encryption_configuration=None,
      clustering=None,
      range_partitioning=None,
      script_options=None,
      job_timeout_ms=None,
      create_session=None,
      connection_properties=None,
      continuous=None,
      **kwds,
  ):
    # pylint: disable=g-doc-args
    """Execute the given query, returning the created job.

    The job will execute synchronously if sync=True is provided as an
    argument or if self.sync is true.

    Args:
      query: Query to execute.
      destination_table: (default None) If provided, send the results to the
        given table.
      create_disposition: Optional. Specifies the create_disposition for the
        destination_table.
      write_disposition: Optional. Specifies the write_disposition for the
        destination_table.
      priority: Optional. Priority to run the query with. Either 'INTERACTIVE'
        (default) or 'BATCH'.
      preserve_nulls: Optional. Indicates whether to preserve nulls in input
        data. Temporary flag; will be removed in a future version.
      allow_large_results: Enables larger destination table sizes.
      dry_run: Optional. Indicates whether the query will only be validated and
        return processing statistics instead of actually running.
      use_cache: Optional. Whether to use the query cache. If create_disposition
        is CREATE_NEVER, will only run the query if the result is already
        cached. Caching is best-effort only and you should not make assumptions
        about whether or how long a query result will be cached.
      min_completion_ratio: Optional. Specifies the minimum fraction of data
        that must be scanned before a query returns. This value should be
        between 0.0 and 1.0 inclusive.
      flatten_results: Whether to flatten nested and repeated fields in the
        result schema. If not set, the default behavior is to flatten.
      external_table_definitions_json: Json representation of external table
        definitions.
      udf_resources: Array of inline and remote UDF resources.
      maximum_billing_tier: Upper limit for billing tier.
      maximum_bytes_billed: Upper limit for bytes billed.
      use_legacy_sql: The choice of using Legacy SQL for the query is optional.
        If not specified, the server will automatically determine the dialect
        based on query information, such as dialect prefixes. If no prefixes are
        found, it will default to Legacy SQL.
      schema_update_options: schema update options when appending to the
        destination table or truncating a table partition.
      labels: an optional dict of labels to set on the query job.
      query_parameters: parameter values for use_legacy_sql=False queries.
      time_partitioning: Optional. Provides time based partitioning
        specification for the destination table.
      clustering: Optional. Provides clustering specification for the
        destination table.
      destination_encryption_configuration: Optional. Allows user to encrypt the
        table created from a query job with a Cloud KMS key.
      range_partitioning: Optional. Provides range partitioning specification
        for the destination table.
      script_options: Optional. Options controlling script execution.
      job_timeout_ms: Optional. How long to let the job run.
      continuous: Optional. Whether the query should be executed as continuous
        query.
      **kwds: Passed on to self.ExecuteJob.

    Raises:
      bq_error.BigqueryClientError: if no query is provided.

    Returns:
      The resulting job info.
    """
    if not query:
      raise bq_error.BigqueryClientError('No query string provided')
    query_config = {'query': query}
    if self.dataset_id:
      query_config['defaultDataset'] = bq_client_utils.GetQueryDefaultDataset(
          self.dataset_id
      )
    if external_table_definitions_json:
      query_config['tableDefinitions'] = external_table_definitions_json
    if udf_resources:
      query_config['userDefinedFunctionResources'] = udf_resources
    if destination_table:
      try:
        reference = bq_client_utils.GetTableReference(
            id_fallbacks=self, identifier=destination_table
        )
      except bq_error.BigqueryError as e:
        raise bq_error.BigqueryError(
            'Invalid value %s for destination_table: %s'
            % (destination_table, e)
        )
      query_config['destinationTable'] = dict(reference)
    if destination_encryption_configuration:
      query_config['destinationEncryptionConfiguration'] = (
          destination_encryption_configuration
      )
    if script_options:
      query_config['scriptOptions'] = script_options
    bq_processor_utils.ApplyParameters(
        query_config,
        allow_large_results=allow_large_results,
        create_disposition=create_disposition,
        preserve_nulls=preserve_nulls,
        priority=priority,
        write_disposition=write_disposition,
        use_query_cache=use_cache,
        flatten_results=flatten_results,
        maximum_billing_tier=maximum_billing_tier,
        maximum_bytes_billed=maximum_bytes_billed,
        use_legacy_sql=use_legacy_sql,
        schema_update_options=schema_update_options,
        query_parameters=query_parameters,
        time_partitioning=time_partitioning,
        clustering=clustering,
        create_session=create_session,
        min_completion_ratio=min_completion_ratio,
        continuous=continuous,
        range_partitioning=range_partitioning,
    )
    bq_processor_utils.ApplyParameters(
        query_config, connection_properties=connection_properties
    )
    request = {'query': query_config}
    bq_processor_utils.ApplyParameters(
        request,
        dry_run=dry_run,
        labels=labels,
        job_timeout_ms=job_timeout_ms,
    )
    return self.ExecuteJob(request, **kwds)

  def Load(
      self,
      destination_table_reference,
      source,
      schema=None,
      create_disposition=None,
      write_disposition=None,
      field_delimiter=None,
      skip_leading_rows=None,
      encoding=None,
      quote=None,
      max_bad_records=None,
      allow_quoted_newlines=None,
      source_format=None,
      allow_jagged_rows=None,
      preserve_ascii_control_characters=None,
      ignore_unknown_values=None,
      projection_fields=None,
      autodetect=None,
      schema_update_options=None,
      null_marker=None,
      time_partitioning=None,
      clustering=None,
      destination_encryption_configuration=None,
      use_avro_logical_types=None,
      reference_file_schema_uri=None,
      range_partitioning=None,
      hive_partitioning_options=None,
      decimal_target_types=None,
      json_extension=None,
      column_name_character_map=None,
      file_set_spec_type=None,
      thrift_options=None,
      parquet_options=None,
      connection_properties=None,
      copy_files_only: Optional[bool] = None,
      **kwds,
  ):
    """Load the given data into BigQuery.

    The job will execute synchronously if sync=True is provided as an
    argument or if self.sync is true.

    Args:
      destination_table_reference: TableReference to load data into.
      source: String specifying source data to load.
      schema: (default None) Schema of the created table. (Can be left blank for
        append operations.)
      create_disposition: Optional. Specifies the create_disposition for the
        destination_table_reference.
      write_disposition: Optional. Specifies the write_disposition for the
        destination_table_reference.
      field_delimiter: Optional. Specifies the single byte field delimiter.
      skip_leading_rows: Optional. Number of rows of initial data to skip.
      encoding: Optional. Specifies character encoding of the input data. May be
        "UTF-8" or "ISO-8859-1". Defaults to UTF-8 if not specified.
      quote: Optional. Quote character to use. Default is '"'. Note that quoting
        is done on the raw binary data before encoding is applied.
      max_bad_records: Optional. Maximum number of bad records that should be
        ignored before the entire job is aborted. Only supported for CSV and
        NEWLINE_DELIMITED_JSON file formats.
      allow_quoted_newlines: Optional. Whether to allow quoted newlines in CSV
        import data.
      source_format: Optional. Format of source data. May be "CSV",
        "DATASTORE_BACKUP", or "NEWLINE_DELIMITED_JSON".
      allow_jagged_rows: Optional. Whether to allow missing trailing optional
        columns in CSV import data.
      preserve_ascii_control_characters: Optional. Whether to preserve embedded
        Ascii Control characters in CSV import data.
      ignore_unknown_values: Optional. Whether to allow extra, unrecognized
        values in CSV or JSON data.
      projection_fields: Optional. If sourceFormat is set to "DATASTORE_BACKUP",
        indicates which entity properties to load into BigQuery from a Cloud
        Datastore backup.
      autodetect: Optional. If true, then we automatically infer the schema and
        options of the source files if they are CSV or JSON formats.
      schema_update_options: schema update options when appending to the
        destination table or truncating a table partition.
      null_marker: Optional. String that will be interpreted as a NULL value.
      time_partitioning: Optional. Provides time based partitioning
        specification for the destination table.
      clustering: Optional. Provides clustering specification for the
        destination table.
      destination_encryption_configuration: Optional. Allows user to encrypt the
        table created from a load job with Cloud KMS key.
      use_avro_logical_types: Optional. Allows user to override default
        behaviour for Avro logical types. If this is set, Avro fields with
        logical types will be interpreted into their corresponding types (ie.
        TIMESTAMP), instead of only using their raw types (ie. INTEGER).
      reference_file_schema_uri: Optional. Allows user to provide a reference
        file with the reader schema, enabled for the format: AVRO, PARQUET, ORC.
      range_partitioning: Optional. Provides range partitioning specification
        for the destination table.
      hive_partitioning_options: (experimental) Options for configuring hive is
        picked if it is in the specified list and if it supports the precision
        and the scale. STRING supports all precision and scale values. If none
        of the listed types supports the precision and the scale, the type
        supporting the widest range in the specified list is picked, and if a
        value exceeds the supported range when reading the data, an error will
        be returned. This field cannot contain duplicate types. The order of the
      decimal_target_types: (experimental) Defines the list of possible SQL data
        types to which the source decimal values are converted. This list and
        the precision and the scale parameters of the decimal field determine
        the target type. In the order of NUMERIC, BIGNUMERIC, and STRING, a type
        is picked if it is in the specified list and if it supports the
        precision and the scale. STRING supports all precision and scale values.
        If none of the listed types supports the precision and the scale, the
        type supporting the widest range in the specified list is picked, and if
        a value exceeds the supported range when reading the data, an error will
        be returned. This field cannot contain duplicate types. The order of the
        types in this field is ignored. For example, ["BIGNUMERIC", "NUMERIC"]
        is the same as ["NUMERIC", "BIGNUMERIC"] and NUMERIC always takes
        precedence over BIGNUMERIC. Defaults to ["NUMERIC", "STRING"] for ORC
        and ["NUMERIC"] for the other file formats.
      json_extension: (experimental) Specify alternative parsing for JSON source
        format. To load newline-delimited JSON, specify 'GEOJSON'. Only
        applicable if `source_format` is 'NEWLINE_DELIMITED_JSON'.
      column_name_character_map: Indicates the character map used for column
        names. Specify 'STRICT' to use the latest character map and reject
        invalid column names. Specify 'V1' to support alphanumeric + underscore
        and name must start with a letter or underscore. Invalid column names
        will be normalized. Specify 'V2' to support flexible column name.
        Invalid column names will be normalized.
      file_set_spec_type: (experimental) Set how to discover files for loading.
        Specify 'FILE_SYSTEM_MATCH' (default behavior) to expand source URIs by
        listing files from the underlying object store. Specify
        'NEW_LINE_DELIMITED_MANIFEST' to parse the URIs as new line delimited
        manifest files, where each line contains a URI (No wild-card URIs are
        supported).
      thrift_options: (experimental) Options for configuring Apache Thrift load,
        which is required if `source_format` is 'THRIFT'.
      parquet_options: Options for configuring parquet files load, only
        applicable if `source_format` is 'PARQUET'.
      connection_properties: Optional. ConnectionProperties for load job.
      copy_files_only: Optional. True to configures the load job to only copy
        files to the destination BigLake managed table, without reading file
        content and writing them to new files.
      **kwds: Passed on to self.ExecuteJob.

    Returns:
      The resulting job info.
    """
    bq_id_utils.typecheck(
        destination_table_reference, bq_id_utils.ApiClientHelper.TableReference
    )
    load_config = {'destinationTable': dict(destination_table_reference)}
    sources = bq_client_utils.ProcessSources(source)
    if sources[0].startswith(bq_processor_utils.GCS_SCHEME_PREFIX):
      load_config['sourceUris'] = sources
      upload_file = None
    else:
      upload_file = sources[0]
    if schema is not None:
      load_config['schema'] = {'fields': bq_client_utils.ReadSchema(schema)}
    if use_avro_logical_types is not None:
      load_config['useAvroLogicalTypes'] = use_avro_logical_types
    if reference_file_schema_uri is not None:
      load_config['reference_file_schema_uri'] = reference_file_schema_uri
    if file_set_spec_type is not None:
      load_config['fileSetSpecType'] = file_set_spec_type
    if json_extension is not None:
      load_config['jsonExtension'] = json_extension
    if column_name_character_map is not None:
      load_config['columnNameCharacterMap'] = column_name_character_map
    if parquet_options is not None:
      load_config['parquetOptions'] = parquet_options
    load_config['decimalTargetTypes'] = decimal_target_types
    if destination_encryption_configuration:
      load_config['destinationEncryptionConfiguration'] = (
          destination_encryption_configuration
      )
    bq_processor_utils.ApplyParameters(
        load_config,
        create_disposition=create_disposition,
        write_disposition=write_disposition,
        field_delimiter=field_delimiter,
        skip_leading_rows=skip_leading_rows,
        encoding=encoding,
        quote=quote,
        max_bad_records=max_bad_records,
        source_format=source_format,
        allow_quoted_newlines=allow_quoted_newlines,
        allow_jagged_rows=allow_jagged_rows,
        preserve_ascii_control_characters=preserve_ascii_control_characters,
        ignore_unknown_values=ignore_unknown_values,
        projection_fields=projection_fields,
        schema_update_options=schema_update_options,
        null_marker=null_marker,
        time_partitioning=time_partitioning,
        clustering=clustering,
        autodetect=autodetect,
        range_partitioning=range_partitioning,
        hive_partitioning_options=hive_partitioning_options,
        thrift_options=thrift_options,
        connection_properties=connection_properties,
        copy_files_only=copy_files_only,
        parquet_options=parquet_options,
    )
    configuration = {'load': load_config}
    return self.ExecuteJob(
        configuration=configuration, upload_file=upload_file, **kwds
    )


  def Extract(
      self,
      reference,
      destination_uris,
      print_header=None,
      field_delimiter=None,
      destination_format=None,
      trial_id=None,
      add_serving_default_signature=None,
      compression=None,
      use_avro_logical_types=None,
      **kwds,
  ):
    """Extract the given table from BigQuery.

    The job will execute synchronously if sync=True is provided as an
    argument or if self.sync is true.

    Args:
      reference: TableReference to read data from.
      destination_uris: String specifying one or more destination locations,
        separated by commas.
      print_header: Optional. Whether to print out a header row in the results.
      field_delimiter: Optional. Specifies the single byte field delimiter.
      destination_format: Optional. Format to extract table to. May be "CSV",
        "AVRO" or "NEWLINE_DELIMITED_JSON".
      trial_id: Optional. 1-based ID of the trial to be exported from a
        hyperparameter tuning model.
      add_serving_default_signature: Optional. Whether to add serving_default
        signature for BigQuery ML trained tf based models.
      compression: Optional. The compression type to use for exported files.
        Possible values include "GZIP" and "NONE". The default value is NONE.
      use_avro_logical_types: Optional. Whether to use avro logical types for
        applicable column types on extract jobs.
      **kwds: Passed on to self.ExecuteJob.

    Returns:
      The resulting job info.

    Raises:
      bq_error.BigqueryClientError: if required parameters are invalid.
    """
    bq_id_utils.typecheck(
        reference,
        (
            bq_id_utils.ApiClientHelper.TableReference,
            bq_id_utils.ApiClientHelper.ModelReference,
        ),
        method='Extract',
    )
    uris = destination_uris.split(',')
    for uri in uris:
      if not uri.startswith(bq_processor_utils.GCS_SCHEME_PREFIX):
        raise bq_error.BigqueryClientError(
            'Illegal URI: {}. Extract URI must start with "{}".'.format(
                uri, bq_processor_utils.GCS_SCHEME_PREFIX
            )
        )
    if isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
      extract_config = {'sourceTable': dict(reference)}
    elif isinstance(reference, bq_id_utils.ApiClientHelper.ModelReference):
      extract_config = {'sourceModel': dict(reference)}
      if trial_id:
        extract_config.update({'modelExtractOptions': {'trialId': trial_id}})
      if add_serving_default_signature:
        extract_config.update({
            'modelExtractOptions': {
                'addServingDefaultSignature': add_serving_default_signature
            }
        })
    bq_processor_utils.ApplyParameters(
        extract_config,
        destination_uris=uris,
        destination_format=destination_format,
        print_header=print_header,
        field_delimiter=field_delimiter,
        compression=compression,
        use_avro_logical_types=use_avro_logical_types,
    )
    configuration = {'extract': extract_config}
    return self.ExecuteJob(configuration=configuration, **kwds)
