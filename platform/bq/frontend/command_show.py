#!/usr/bin/env python
"""The show command for the BQ CLI."""

from typing import Optional

from absl import app
from absl import flags

from frontend import bigquery_command
from frontend import bq_cached_client
from frontend import utils as bq_frontend_utils
from utils import bq_id_utils

FLAGS = flags.FLAGS
ApiClientHelper = bq_id_utils.ApiClientHelper
DatasetReference = bq_id_utils.ApiClientHelper.DatasetReference
TransferConfigReference = bq_id_utils.ApiClientHelper.TransferConfigReference
TransferRunReference = bq_id_utils.ApiClientHelper.TransferRunReference
EncryptionServiceAccount = (
    bq_id_utils.ApiClientHelper.EncryptionServiceAccount)


class Show(bigquery_command.BigqueryCmd):
  """The BQ CLI command to display a resource to the user."""
  usage = """show [<identifier>]"""

  def __init__(self, name: str, fv: flags.FlagValues) -> None:
    super(Show, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'job',
        False,
        'If true, interpret this identifier as a job id.',
        short_name='j',
        flag_values=fv)
    flags.DEFINE_boolean(
        'dataset',
        False,
        'Show dataset with this name.',
        short_name='d',
        flag_values=fv)
    flags.DEFINE_boolean(
        'view',
        False,
        'Show view specific details instead of general table details.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'materialized_view',
        False,
        'Show materialized view specific details instead of general table '
        'details.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'table_replica',
        False,
        'Show table replica specific details instead of general table details.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'schema',
        False,
        'Show only the schema instead of general table details.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'encryption_service_account',
        False,
        'Show the service account for a user if it exists, or create one '
        'if it does not exist.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'transfer_config',
        False,
        'Show transfer configuration for configuration resource name.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'transfer_run',
        False,
        'Show information about the particular transfer run.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'model',
        False,
        'Show details of model with this model ID.',
        short_name='m',
        flag_values=fv)
    flags.DEFINE_boolean(
        'routine',
        False,
        'Show the details of a particular routine.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation',
        None,
        'Shows details for the reservation described by this identifier.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'capacity_commitment',
        None, 'Shows details for the capacity commitment described by this '
        'identifier.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation_assignment',
        None, 'Looks up reservation assignments for a specified '
        'project/folder/organization. Explicit reservation assignments will be '
        'returned if exist. Otherwise implicit reservation assignments from '
        'parents will be returned. '
        'Used in conjunction with --job_type, --assignee_type and '
        '--assignee_id.',
        flag_values=fv)
    flags.DEFINE_enum(
        'job_type',
        None,
        [
            'QUERY',
            'PIPELINE',
            'ML_EXTERNAL',
            'BACKGROUND',
            'SPARK',
            'CONTINUOUS',
        ],
        (
            'Type of jobs to search reservation assignment for. Options'
            ' include:\n QUERY\n PIPELINE\n ML_EXTERNAL\n BACKGROUND\n SPARK\n'
            ' Used in conjunction with --reservation_assignment.'
        ),
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'assignee_type',
        None, ['PROJECT', 'FOLDER', 'ORGANIZATION'],
        'Type of assignees for the reservation assignment. Options include:'
        '\n PROJECT'
        '\n FOLDER'
        '\n ORGANIZATION'
        '\n Used in conjunction with --reservation_assignment.',
        flag_values=fv)
    flags.DEFINE_string(
        'assignee_id',
        None,
        'Project/folder/organization ID, to which the reservation is assigned. '
        'Used in conjunction with --reservation_assignment.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'connection',
        None,
        'Shows details for the connection described by this identifier.',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier: str = '') -> Optional[int]:
    """Show all information about an object.

    Examples:
      bq show -j <job_id>
      bq show dataset
      bq show [--schema] dataset.table
      bq show [--view] dataset.view
      bq show [--materialized_view] dataset.materialized_view
      bq show -m ds.model
      bq show --routine ds.routine
      bq show --transfer_config projects/p/locations/l/transferConfigs/c
      bq show --transfer_run projects/p/locations/l/transferConfigs/c/runs/r
      bq show --encryption_service_account
      bq show --connection --project_id=project --location=us connection
      bq show --capacity_commitment project:US.capacity_commitment_id
      bq show --reservation --location=US --project_id=project reservation_name
      bq show --reservation_assignment --project_id=project --location=US
          --assignee_type=PROJECT --assignee_id=myproject --job_type=QUERY
      bq show --reservation_assignment --project_id=project --location=US
          --assignee_type=FOLDER --assignee_id=123 --job_type=QUERY
      bq show --reservation_assignment --project_id=project --location=US
          --assignee_type=ORGANIZATION --assignee_id=456 --job_type=QUERY

    Arguments:
      identifier: the identifier of the resource to show.
    """
    # pylint: disable=g-doc-exception
    client = bq_cached_client.Client.Get()
    custom_format = 'show'
    object_info = None
    print_reference = True
    if self.j:
      reference = client.GetJobReference(identifier, FLAGS.location)
    elif self.d:
      reference = client.GetDatasetReference(identifier)
    elif self.view:
      reference = client.GetTableReference(identifier)
      custom_format = 'view'
    elif self.materialized_view:
      reference = client.GetTableReference(identifier)
      custom_format = 'materialized_view'
    elif self.table_replica:
      reference = client.GetTableReference(identifier)
      custom_format = 'table_replica'
    elif self.schema:
      if FLAGS.format not in [None, 'prettyjson', 'json']:
        raise app.UsageError(
            'Table schema output format must be json or prettyjson.')
      reference = client.GetTableReference(identifier)
      custom_format = 'schema'
    elif self.transfer_config:
      formatted_identifier = bq_id_utils.FormatDataTransferIdentifiers(
          client, identifier
      )
      reference = TransferConfigReference(
          transferConfigName=formatted_identifier)
      object_info = client.GetTransferConfig(formatted_identifier)
    elif self.transfer_run:
      formatted_identifier = bq_id_utils.FormatDataTransferIdentifiers(
          client, identifier
      )
      reference = TransferRunReference(transferRunName=formatted_identifier)
      object_info = client.GetTransferRun(formatted_identifier)
    elif self.m:
      reference = client.GetModelReference(identifier)
    elif self.routine:
      reference = client.GetRoutineReference(identifier)
    elif self.reservation:
      reference = client.GetReservationReference(
          identifier=identifier, default_location=FLAGS.location)
      object_info = client.GetReservation(reference)
    elif self.reservation_assignment:
      search_all_projects = True
      if search_all_projects:
        object_info = client.SearchAllReservationAssignments(
            location=FLAGS.location,
            job_type=self.job_type,
            assignee_type=self.assignee_type,
            assignee_id=self.assignee_id)
      # Here we just need any object of ReservationAssignmentReference type, but
      # the value of the object doesn't matter here.
      # PrintObjectInfo() will use the type and object_info to format the
      # output.
      reference = ApiClientHelper.ReservationAssignmentReference.Create(
          projectId=' ',
          location=' ',
          reservationId=' ',
          reservationAssignmentId=' ')
      print_reference = False
    elif self.capacity_commitment:
      reference = client.GetCapacityCommitmentReference(
          identifier=identifier, default_location=FLAGS.location)
      object_info = client.GetCapacityCommitment(reference)
    elif self.encryption_service_account:
      object_info = client.apiclient.projects().getServiceAccount(
          projectId=client.GetProjectReference().projectId).execute()
      email = object_info['email']
      object_info = {'ServiceAccountID': email}
      reference = EncryptionServiceAccount(serviceAccount='serviceAccount')
    elif self.connection:
      reference = client.GetConnectionReference(
          identifier, default_location=FLAGS.location)
      object_info = client.GetConnection(reference)
    else:
      reference = client.GetReference(identifier)
    if reference is None:
      raise app.UsageError('Must provide an identifier for show.')

    if object_info is None:
      object_info = client.GetObjectInfo(reference)
    bq_frontend_utils.PrintObjectInfo(
        object_info,
        reference,
        custom_format=custom_format,
        print_reference=print_reference,
    )
