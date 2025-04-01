#!/usr/bin/env python
"""BigqueryClientExtended class. Legacy code."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Any, Optional

from clients import bigquery_client
from clients import client_data_transfer
from clients import client_dataset
from clients import client_job
from clients import client_model
from clients import client_project
from clients import client_table
from clients import utils as bq_client_utils
from clients import wait_printer
from frontend import utils_formatting
from utils import bq_api_utils
from utils import bq_error
from utils import bq_id_utils
from utils import bq_processor_utils

Service = bq_api_utils.Service


class BigqueryClientExtended(bigquery_client.BigqueryClient):
  """Class extending BigqueryClient to add resource specific functionality."""


  def GetObjectInfo(self, reference):
    """Get all data returned by the server about a specific object."""
    # Projects are handled separately, because we only have
    # bigquery.projects.list.
    if isinstance(reference, bq_id_utils.ApiClientHelper.ProjectReference):
      max_project_results = 1000
      projects = client_project.list_projects(
          apiclient=self.apiclient, max_results=max_project_results
      )
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
      request = dict(reference)
      request['accessPolicyVersion'] = (
          bq_client_utils.MAX_SUPPORTED_IAM_POLICY_VERSION
      )
      return self.apiclient.datasets().get(**request).execute()
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
      raise bq_error.BigqueryTypeError(
          'Type of reference must be one of: ProjectReference, '
          'JobReference, DatasetReference, or TableReference'
      )

