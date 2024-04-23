#!/usr/bin/env python
"""The BigQuery delete CLI command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Optional


from absl import app
from absl import flags

from clients import client_dataset
from frontend import bigquery_command
from frontend import bq_cached_client
from frontend import utils as frontend_utils
from utils import bq_error
from utils import bq_id_utils

FLAGS = flags.FLAGS

# These aren't relevant for user-facing docstrings:
# pylint: disable=g-doc-return-or-yield
# pylint: disable=g-doc-args


class Delete(bigquery_command.BigqueryCmd):
  usage = """rm [-f] [-r] [(-d|-t)] <identifier>"""

  def __init__(self, name: str, fv: flags.FlagValues):
    super(Delete, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'dataset',
        False,
        'Remove dataset described by this identifier.',
        short_name='d',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'table',
        False,
        'Remove table described by this identifier.',
        short_name='t',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'job',
        False,
        'Remove job described by this identifier.',
        short_name='j',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'transfer_config',
        False,
        'Remove transfer configuration described by this identifier.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'force',
        None,
        "Ignore existing tables and datasets, don't prompt.",
        short_name='f',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'recursive',
        False,
        'Remove dataset and any tables it may contain.',
        short_name='r',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'reservation',
        False,
        'Deletes the reservation described by this identifier.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'capacity_commitment',
        False,
        'Deletes the capacity commitment described by this identifier.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'reservation_assignment',
        False,
        'Delete a reservation assignment.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'model',
        False,
        'Remove model with this model ID.',
        short_name='m',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'routine', False, 'Remove routine with this routine ID.', flag_values=fv
    )
    flags.DEFINE_boolean(
        'connection', False, 'Delete a connection.', flag_values=fv
    )
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier: str) -> Optional[int]:
    """Delete the resource described by the identifier.

    Always requires an identifier, unlike the show and ls commands.
    By default, also requires confirmation before deleting. Supports
    the -d -t flags to signify that the identifier is a dataset
    or table.
     * With -f, don't ask for confirmation before deleting.
     * With -r, remove all tables in the named dataset.

    Examples:
      bq rm ds.table
      bq rm -m ds.model
      bq rm --routine ds.routine
      bq rm -r -f old_dataset
      bq rm --transfer_config=projects/p/locations/l/transferConfigs/c
      bq rm --connection --project_id=proj --location=us con
      bq rm --capacity_commitment proj:US.capacity_commitment_id
      bq rm --reservation --project_id=proj --location=us reservation_name
      bq rm --reservation_assignment --project_id=proj --location=us
          assignment_name
    """

    client = bq_cached_client.Client.Get()

    # pylint: disable=g-doc-exception
    if (
        self.d
        + self.t
        + self.j
        + self.routine
        + self.transfer_config
        + self.reservation
        + self.reservation_assignment
        + self.capacity_commitment
        + self.connection
    ) > 1:
      raise app.UsageError('Cannot specify more than one resource type.')
    if not identifier:
      raise app.UsageError('Must provide an identifier for rm.')

    if self.t:
      reference = client.GetTableReference(identifier)
    elif self.m:
      reference = client.GetModelReference(identifier)
    elif self.routine:
      reference = client.GetRoutineReference(identifier)
    elif self.d:
      reference = client.GetDatasetReference(identifier)
    elif self.j:
      reference = client.GetJobReference(
          identifier, default_location=FLAGS.location
      )
    elif self.transfer_config:
      formatted_identifier = bq_id_utils.FormatDataTransferIdentifiers(
          client, identifier
      )
      reference = bq_id_utils.ApiClientHelper.TransferConfigReference(
          transferConfigName=formatted_identifier
      )
    elif self.reservation:
      try:
        reference = client.GetReservationReference(
            identifier=identifier, default_location=FLAGS.location
        )
        client.DeleteReservation(
            reference
        )
        print("Reservation '%s' successfully deleted." % identifier)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to delete reservation '%s': %s" % (identifier, e)
        )
    elif self.reservation_assignment:
      try:
        reference = client.GetReservationAssignmentReference(
            identifier=identifier, default_location=FLAGS.location
        )
        client.DeleteReservationAssignment(reference)
        print("Reservation assignment '%s' successfully deleted." % identifier)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to delete reservation assignment '%s': %s" % (identifier, e)
        )
    elif self.capacity_commitment:
      try:
        reference = client.GetCapacityCommitmentReference(
            identifier=identifier, default_location=FLAGS.location
        )
        client.DeleteCapacityCommitment(reference, self.force)
        print("Capacity commitment '%s' successfully deleted." % identifier)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to delete capacity commitment '%s': %s" % (identifier, e)
        )
    elif self.connection:
      reference = client.GetConnectionReference(
          identifier=identifier, default_location=FLAGS.location
      )
      client.DeleteConnection(reference)
    else:
      reference = client.GetReference(identifier)
      bq_id_utils.typecheck(
          reference,
          (
              bq_id_utils.ApiClientHelper.DatasetReference,
              bq_id_utils.ApiClientHelper.TableReference,
          ),
          'Invalid identifier "%s" for rm.' % (identifier,),
          is_usage_error=True,
      )

    if (
        isinstance(reference, bq_id_utils.ApiClientHelper.TableReference)
        and self.r
    ):
      raise app.UsageError('Cannot specify -r with %r' % (reference,))

    if (
        isinstance(reference, bq_id_utils.ApiClientHelper.ModelReference)
        and self.r
    ):
      raise app.UsageError('Cannot specify -r with %r' % (reference,))

    if (
        isinstance(reference, bq_id_utils.ApiClientHelper.RoutineReference)
        and self.r
    ):
      raise app.UsageError('Cannot specify -r with %r' % (reference,))

    if not self.force:
      if (
          (
              isinstance(
                  reference, bq_id_utils.ApiClientHelper.DatasetReference
              )
              and client.DatasetExists(reference)
          )
          or (
              isinstance(reference, bq_id_utils.ApiClientHelper.TableReference)
              and client.TableExists(reference)
          )
          or (
              isinstance(reference, bq_id_utils.ApiClientHelper.JobReference)
              and client.JobExists(reference)
          )
          or (
              isinstance(reference, bq_id_utils.ApiClientHelper.ModelReference)
              and client.ModelExists(reference)
          )
          or (
              isinstance(
                  reference, bq_id_utils.ApiClientHelper.RoutineReference
              )
              and client.RoutineExists(reference)
          )
          or (
              isinstance(
                  reference, bq_id_utils.ApiClientHelper.TransferConfigReference
              )
              and client.TransferExists(reference)
          )
      ):
        if 'y' != frontend_utils.PromptYN(
            'rm: remove %r? (y/N) ' % (reference,)
        ):
          print('NOT deleting %r, exiting.' % (reference,))
          return 0

    if isinstance(reference, bq_id_utils.ApiClientHelper.DatasetReference):
      client_dataset.DeleteDataset(
          client.apiclient,
          reference,
          ignore_not_found=self.force,
          delete_contents=self.recursive,
      )
    elif isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
      client.DeleteTable(reference, ignore_not_found=self.force)
    elif isinstance(reference, bq_id_utils.ApiClientHelper.JobReference):
      client.DeleteJob(reference, ignore_not_found=self.force)
    elif isinstance(reference, bq_id_utils.ApiClientHelper.ModelReference):
      client.DeleteModel(reference, ignore_not_found=self.force)
    elif isinstance(reference, bq_id_utils.ApiClientHelper.RoutineReference):
      client.DeleteRoutine(reference, ignore_not_found=self.force)
    elif isinstance(
        reference, bq_id_utils.ApiClientHelper.TransferConfigReference
    ):
      client.DeleteTransferConfig(reference, ignore_not_found=self.force)
