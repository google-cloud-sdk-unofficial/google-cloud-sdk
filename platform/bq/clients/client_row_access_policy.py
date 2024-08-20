#!/usr/bin/env python
"""The BigQuery CLI row access policy client library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Any, Dict, List



# To configure apiclient logging.
from google.api_core import iam

from clients import bigquery_client
from utils import bq_id_utils

# IAM role name that represents being a grantee on a row access policy.
_FILTERED_DATA_VIEWER_ROLE = 'roles/bigquery.filteredDataViewer'


def _list_row_access_policies(
    bqclient: bigquery_client.BigqueryClient,
    table_reference: 'bq_id_utils.ApiClientHelper.TableReference',
    page_size: int,
    page_token: str,
) -> Dict[str, List[Any]]:
  """Lists row access policies for the given table reference."""
  return (
      bqclient.GetRowAccessPoliciesApiClient()
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


def list_row_access_policies_with_grantees(
    bqclient: bigquery_client.BigqueryClient,
    table_reference: 'bq_id_utils.ApiClientHelper.TableReference',
    page_size: int,
    page_token: str,
    max_concurrent_iam_calls: int = 1,
) -> Dict[str, List[Any]]:
  """Lists row access policies for the given table reference.

  Arguments:
    bqclient: BigQuery client to use for the request.
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
  response = _list_row_access_policies(
      bqclient=bqclient,
      table_reference=table_reference,
      page_size=page_size,
      page_token=page_token,
  )
  if 'rowAccessPolicies' in response:
    row_access_policies = response['rowAccessPolicies']
    for row_access_policy in row_access_policies:
      _set_row_access_policy_grantees(
          bqclient=bqclient,
          row_access_policy=row_access_policy,
      )
  return response


def _set_row_access_policy_grantees(
    bqclient: bigquery_client.BigqueryClient, row_access_policy
):
  """Sets the grantees on the given Row Access Policy."""
  row_access_policy_ref = (
      bq_id_utils.ApiClientHelper.RowAccessPolicyReference.Create(
          **row_access_policy['rowAccessPolicyReference']
      )
  )
  iam_policy = get_row_access_policy_iam_policy(
      bqclient=bqclient, reference=row_access_policy_ref
  )
  grantees = _get_grantees_from_row_access_policy_iam_policy(iam_policy)
  row_access_policy['grantees'] = grantees


def _get_grantees_from_row_access_policy_iam_policy(iam_policy):
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


def get_row_access_policy_iam_policy(
    bqclient: bigquery_client.BigqueryClient,
    reference: 'bq_id_utils.ApiClientHelper.RowAccessPolicyReference',
) -> iam.Policy:
  """Gets IAM policy for the given row access policy resource.

  Arguments:
    bqclient: BigQuery client to use for the request.
    reference: the RowAccessPolicyReference for the row access policy resource.

  Returns:
    The IAM policy attached to the given row access policy resource.

  Raises:
    TypeError: if reference is not a RowAccessPolicyReference.
  """
  bq_id_utils.typecheck(
      reference,
      bq_id_utils.ApiClientHelper.RowAccessPolicyReference,
      method='get_row_access_policy_iam_policy',
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
      bqclient.GetIAMPolicyApiClient()
      .rowAccessPolicies()
      .getIamPolicy(resource=formatted_resource)
      .execute()
  )
