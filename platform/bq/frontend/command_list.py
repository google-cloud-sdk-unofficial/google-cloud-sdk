#!/usr/bin/env python
"""The BigQuery list CLI command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Optional

from absl import app
from absl import flags

from frontend import bigquery_command
from frontend import bq_cached_client
from frontend import utils as frontend_utils
from utils import bq_error
from utils import bq_id_utils

FLAGS = flags.FLAGS

# These aren't relevant for user-facing docstrings:
# pylint: disable=g-doc-return-or-yield
# pylint: disable=g-doc-args


class ListCmd(bigquery_command.BigqueryCmd):  # pylint: disable=missing-docstring
  usage = """ls [(-j|-p|-d)] [-a] [-n <number>] [<identifier>]"""

  def __init__(self, name: str, fv: flags.FlagValues):
    super(ListCmd, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'all',
        None,
        'Show all results. For jobs, will show jobs from all users. For '
        'datasets, will list hidden datasets.'
        'For transfer configs and runs, '
        'this flag is redundant and not necessary.'
        '',
        short_name='a',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'all_jobs', None, 'DEPRECATED. Use --all instead', flag_values=fv
    )
    flags.DEFINE_boolean(
        'jobs',
        False,
        'Show jobs described by this identifier.',
        short_name='j',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'max_results',
        None,
        'Maximum number to list.',
        short_name='n',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'min_creation_time',
        None,
        'Timestamp in milliseconds. Return jobs created after this timestamp.',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'max_creation_time',
        None,
        'Timestamp in milliseconds. Return jobs created before this timestamp.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'projects', False, 'Show all projects.', short_name='p', flag_values=fv
    )
    flags.DEFINE_boolean(
        'datasets',
        False,
        'Show datasets described by this identifier.',
        short_name='d',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'models', False, 'Show all models.', short_name='m', flag_values=fv
    )
    flags.DEFINE_boolean(
        'routines', False, 'Show all routines.', flag_values=fv
    )
    flags.DEFINE_boolean(
        'row_access_policies',
        False,
        'Show all row access policies.',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'transfer_location',
        None,
        'Location for list transfer config (e.g., "eu" or "us").',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'transfer_config',
        False,
        'Show transfer configurations described by this identifier. '
        'This requires setting --transfer_location.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'transfer_run', False, 'List the transfer runs.', flag_values=fv
    )
    flags.DEFINE_string(
        'run_attempt',
        'LATEST',
        'For transfer run, respresents which runs should be '
        'pulled. See https://cloud.google.com/bigquery/docs/reference/'
        'datatransfer/rest/v1/projects.transferConfigs.runs/list#RunAttempt '
        'for details',
        flag_values=fv,
    )
    flags.DEFINE_bool(
        'transfer_log',
        False,
        'List messages under the run specified',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'message_type',
        None,
        'usage:- messageTypes:INFO '
        'For transferlog, represents which messages should '
        'be listed. See '
        'https://cloud.google.com/bigquery/docs/reference'
        '/datatransfer/rest/v1/projects.transferConfigs'
        '.runs.transferLogs#MessageSeverity '
        'for details.',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'page_token',
        None,
        'Start listing from this page token.',
        short_name='k',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'print_last_token',
        False,
        'If true, also print the next page token for the jobs list.',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'filter',
        None,
        'Filters resources based on the filter expression.'
        '\nFor datasets, use a space-separated list of label keys and values '
        'in the form "labels.key:value". Datasets must match '
        'all provided filter expressions. See '
        'https://cloud.google.com/bigquery/docs/filtering-labels'
        '#filtering_datasets_using_labels '
        'for details'
        '\nFor transfer configurations, the filter expression, '
        'in the form "dataSourceIds:value(s)", will show '
        'transfer configurations with '
        ' the specified dataSourceId. '
        '\nFor transfer runs, the filter expression, '
        'in the form "states:VALUE(s)", will show '
        'transfer runs with the specified states. See '
        'https://cloud.google.com/bigquery/docs/reference/datatransfer/rest/v1/'
        'TransferState '
        'for details.'
        '\nFor jobs, filtering is currently not supported.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'reservation',
        None,
        'List all reservations for the given project and location.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'capacity_commitment',
        None,
        'Lists all capacity commitments (e.g. slots) for the given project and '
        'location.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'reservation_assignment',
        None,
        'List all reservation assignments for given project/location',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'parent_job_id',
        None,
        'Only show jobs which are children of this parent job; if omitted, '
        'shows all jobs which have no parent.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'connection',
        None,
        'List all connections for given project/location',
        flag_values=fv,
    )
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier: str = '') -> Optional[int]:
    """List the objects contained in the named collection.

    List the objects in the named project or dataset. A trailing : or
    . can be used to signify a project or dataset.
     * With -j, show the jobs in the named project.
     * With -p, show all projects.

    Examples:
      bq ls
      bq ls -j proj
      bq ls -p -n 1000
      bq ls mydataset
      bq ls -a
      bq ls -m mydataset
      bq ls --routines mydataset
      bq ls --row_access_policies mytable (requires whitelisting)
      bq ls --filter labels.color:red
      bq ls --filter 'labels.color:red labels.size:*'
      bq ls --transfer_config --transfer_location='us'
          --filter='dataSourceIds:play,adwords'
      bq ls --transfer_run --filter='states:SUCCESSED,PENDING'
          --run_attempt='LATEST' projects/p/locations/l/transferConfigs/c
      bq ls --transfer_log --message_type='messageTypes:INFO,ERROR'
          projects/p/locations/l/transferConfigs/c/runs/r
      bq ls --capacity_commitment --project_id=proj --location='us'
      bq ls --reservation --project_id=proj --location='us'
      bq ls --reservation_assignment --project_id=proj --location='us'
      bq ls --reservation_assignment --project_id=proj --location='us'
          <reservation_id>
      bq ls --connection --project_id=proj --location=us
    """

    # pylint: disable=g-doc-exception
    if frontend_utils.ValidateAtMostOneSelected(self.j, self.p, self.d):
      raise app.UsageError('Cannot specify more than one of -j, -p, or -d.')
    if self.p and identifier:
      raise app.UsageError('Cannot specify an identifier with -p')

    # Copy deprecated flag specifying 'all' to current one.
    if self.all_jobs is not None:
      self.a = self.all_jobs

    client = bq_cached_client.Client.Get()
    if identifier:
      reference = client.GetReference(identifier)
    else:
      try:
        reference = client.GetReference(identifier)
      except bq_error.BigqueryError:
        # We want to let through the case of no identifier, which
        # will fall through to the second case below.
        reference = None

    if self.row_access_policies:
      bq_id_utils.typecheck(
          reference,
          bq_id_utils.ApiClientHelper.TableReference,
          (
              'Invalid identifier "%s" for ls, cannot list row access '
              'policies on object of type %s'
          )
          % (identifier, type(reference).__name__),
          is_usage_error=True,
      )
    else:
      # If we got a TableReference, we might be able to make sense
      # of it as a DatasetReference, as in 'ls foo' with dataset_id
      # set.
      if isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
        try:
          reference = client.GetDatasetReference(identifier)
        except bq_error.BigqueryError:
          pass
      bq_id_utils.typecheck(
          reference,
          (
              type(None),
              bq_id_utils.ApiClientHelper.ProjectReference,
              bq_id_utils.ApiClientHelper.DatasetReference,
          ),
          (
              'Invalid identifier "%s" for ls, cannot call list on object '
              'of type %s'
          )
          % (identifier, type(reference).__name__),
          is_usage_error=True,
      )

    if self.d and isinstance(
        reference, bq_id_utils.ApiClientHelper.DatasetReference
    ):
      reference = reference.GetProjectReference()

    page_token = self.k
    results = None
    object_type = None
    if self.j:
      object_type = bq_id_utils.ApiClientHelper.JobReference
      reference = client.GetProjectReference(identifier)
      bq_id_utils.typecheck(
          reference,
          bq_id_utils.ApiClientHelper.ProjectReference,
          'Cannot determine job(s) associated with "%s"' % (identifier,),
          is_usage_error=True,
      )
      if self.print_last_token:
        results = client.ListJobsAndToken(
            reference=reference,
            max_results=self.max_results,
            all_users=self.a,
            min_creation_time=self.min_creation_time,
            max_creation_time=self.max_creation_time,
            page_token=page_token,
            parent_job_id=self.parent_job_id,
        )
        assert object_type is not None
        frontend_utils.PrintObjectsArrayWithToken(results, object_type)
        return
      results = client.ListJobs(
          reference=reference,
          max_results=self.max_results,
          all_users=self.a,
          min_creation_time=self.min_creation_time,
          max_creation_time=self.max_creation_time,
          page_token=page_token,
          parent_job_id=self.parent_job_id,
      )
    elif self.m:
      object_type = bq_id_utils.ApiClientHelper.ModelReference
      reference = client.GetDatasetReference(identifier)
      response = client.ListModels(
          reference=reference,
          max_results=self.max_results,
          page_token=page_token,
      )
      if 'models' in response:
        results = response['models']
      if 'nextPageToken' in response:
        frontend_utils.PrintPageToken(response)
    elif self.routines:
      object_type = bq_id_utils.ApiClientHelper.RoutineReference
      reference = client.GetDatasetReference(identifier)
      response = client.ListRoutines(
          reference=reference,
          max_results=self.max_results,
          page_token=page_token,
          filter_expression=self.filter,
      )
      if 'routines' in response:
        results = response['routines']
      if 'nextPageToken' in response:
        frontend_utils.PrintPageToken(response)
    elif self.reservation_assignment:
      try:
        if FLAGS.api_version == 'v1beta1':
          object_type = (
              bq_id_utils.ApiClientHelper.BetaReservationAssignmentReference
          )
        else:
          object_type = (
              bq_id_utils.ApiClientHelper.ReservationAssignmentReference
          )
        reference = client.GetReservationReference(
            identifier=identifier if identifier else '-',
            default_location=FLAGS.location,
            default_reservation_id=' ',
        )
        response = client.ListReservationAssignments(
            reference, self.max_results, self.page_token
        )
        if 'assignments' in response:
          results = response['assignments']
        else:
          print('No reservation assignments found.')
        if 'nextPageToken' in response:
          frontend_utils.PrintPageToken(response)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list reservation assignments '%s': %s" % (identifier, e)
        )
    elif self.capacity_commitment:
      try:
        object_type = bq_id_utils.ApiClientHelper.CapacityCommitmentReference
        reference = client.GetCapacityCommitmentReference(
            identifier=identifier,
            default_location=FLAGS.location,
            default_capacity_commitment_id=' ',
        )
        response = client.ListCapacityCommitments(
            reference, self.max_results, self.page_token
        )
        if 'capacityCommitments' in response:
          results = response['capacityCommitments']
        else:
          print('No capacity commitments found.')
        if 'nextPageToken' in response:
          frontend_utils.PrintPageToken(response)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list capacity commitments '%s': %s" % (identifier, e)
        )
    elif self.reservation:
      response = None
      if FLAGS.api_version == 'v1beta1':
        object_type = bq_id_utils.ApiClientHelper.BetaReservationReference
      else:
        object_type = bq_id_utils.ApiClientHelper.ReservationReference
      reference = client.GetReservationReference(
          identifier=identifier,
          default_location=FLAGS.location,
          default_reservation_id=' ',
      )
      try:
        if True:
          response = client.ListBiReservations(reference)
          results = [response]
        if response and 'size' in response:
          size_in_bytes = int(response['size'])
          size_in_gbytes = size_in_bytes / (1024 * 1024 * 1024)
          print('BI Engine reservation: %sGB' % size_in_gbytes)
      except bq_error.BigqueryNotFoundError:
        pass
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list BI reservations '%s': %s" % (identifier, e)
        )

      try:
        if True:
          response = client.ListReservations(
              reference=reference,
              page_size=self.max_results,
              page_token=self.page_token,
          )
          results = (
              response['reservations'] if 'reservations' in response else []
          )
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list reservations '%s': %s" % (identifier, e)
        )
      if not results:
        print('No reservations found.')
      if response and 'nextPageToken' in response:
        frontend_utils.PrintPageToken(response)
    elif self.transfer_config:
      object_type = bq_id_utils.ApiClientHelper.TransferConfigReference
      reference = client.GetProjectReference(
          bq_id_utils.FormatProjectIdentifier(client, identifier)
      )
      bq_id_utils.typecheck(
          reference,
          bq_id_utils.ApiClientHelper.ProjectReference,
          'Cannot determine transfer configuration(s) associated with "%s"'
          % (identifier,),
          is_usage_error=True,
      )

      if self.transfer_location is None:
        raise app.UsageError(
            'Need to specify transfer_location for list transfer configs.'
        )

      # transfer_configs tuple contains transfer configs at index 0 and
      # next page token at index 1 if there is one.
      transfer_configs = client.ListTransferConfigs(
          reference=reference,
          location=self.transfer_location,
          page_size=self.max_results,
          page_token=page_token,
          data_source_ids=self.filter,
      )
      # If the max_results flag is set and the length of transfer_configs is 2
      # then it also contains the next_page_token.
      if self.max_results and len(transfer_configs) == 2:
        page_token = dict(nextPageToken=transfer_configs[1])
        frontend_utils.PrintPageToken(page_token)
      results = transfer_configs[0]
    elif self.transfer_run:
      object_type = bq_id_utils.ApiClientHelper.TransferRunReference
      run_attempt = self.run_attempt
      formatted_identifier = bq_id_utils.FormatDataTransferIdentifiers(
          client, identifier
      )
      reference = bq_id_utils.ApiClientHelper.TransferRunReference(
          transferRunName=formatted_identifier
      )
      # list_transfer_runs_result tuple contains transfer runs at index 0 and
      # next page token at index 1 if there is next page token.
      list_transfer_runs_result = client.ListTransferRuns(
          reference,
          run_attempt,
          max_results=self.max_results,
          page_token=self.page_token,
          states=self.filter,
      )
      # If the max_results flag is set and the length of response is 2
      # then it also contains the next_page_token.
      if self.max_results and len(list_transfer_runs_result) == 2:
        page_token = dict(nextPageToken=list_transfer_runs_result[1])
        frontend_utils.PrintPageToken(page_token)
      results = list_transfer_runs_result[0]
    elif self.transfer_log:
      object_type = bq_id_utils.ApiClientHelper.TransferLogReference
      formatted_identifier = bq_id_utils.FormatDataTransferIdentifiers(
          client, identifier
      )
      reference = bq_id_utils.ApiClientHelper.TransferLogReference(
          transferRunName=formatted_identifier
      )
      # list_transfer_log_result tuple contains transfer logs at index 0 and
      # next page token at index 1 if there is one.
      list_transfer_log_result = client.ListTransferLogs(
          reference,
          message_type=self.message_type,
          max_results=self.max_results,
          page_token=self.page_token,
      )
      if self.max_results and len(list_transfer_log_result) == 2:
        page_token = dict(nextPageToken=list_transfer_log_result[1])
        frontend_utils.PrintPageToken(page_token)
      results = list_transfer_log_result[0]
    elif self.connection:
      object_type = bq_id_utils.ApiClientHelper.ConnectionReference
      list_connections_results = client.ListConnections(
          FLAGS.project_id,
          FLAGS.location,
          max_results=self.max_results,
          page_token=self.page_token,
      )
      if 'connections' in list_connections_results:
        results = list_connections_results['connections']
      else:
        print('No connections found.')
      if 'nextPageToken' in list_connections_results:
        frontend_utils.PrintPageToken(list_connections_results)
    elif self.row_access_policies:
      object_type = bq_id_utils.ApiClientHelper.RowAccessPolicyReference
      response = client.ListRowAccessPoliciesWithGrantees(
          reference,
          self.max_results,
          self.page_token,
      )
      if 'rowAccessPolicies' in response:
        results = response['rowAccessPolicies']
      else:
        print('No row access policies found.')
      if 'nextPageToken' in response:
        frontend_utils.PrintPageToken(response)
    elif self.d:
      reference = client.GetProjectReference(identifier)
      object_type = bq_id_utils.ApiClientHelper.DatasetReference
      results = client.ListDatasets(
          reference,
          max_results=self.max_results,
          list_all=self.a,
          page_token=page_token,
          filter_expression=self.filter,
      )
    elif self.p or reference is None:
      object_type = bq_id_utils.ApiClientHelper.ProjectReference
      results = client.ListProjects(
          max_results=self.max_results, page_token=page_token
      )
    elif isinstance(reference, bq_id_utils.ApiClientHelper.ProjectReference):
      object_type = bq_id_utils.ApiClientHelper.DatasetReference
      results = client.ListDatasets(
          reference,
          max_results=self.max_results,
          list_all=self.a,
          page_token=page_token,
          filter_expression=self.filter,
      )
    else:  # isinstance(reference, DatasetReference):
      object_type = bq_id_utils.ApiClientHelper.TableReference
      results = client.ListTables(
          reference, max_results=self.max_results, page_token=page_token
      )
    if results:
      assert object_type is not None
      frontend_utils.PrintObjectsArray(results, object_type)
