# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Creates a new Backup Plan."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.backupdr.backup_plans import BackupPlansClient
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class Create(base.CreateCommand):
  """Creates a new Backup Plan."""

  detailed_help = {
      'BRIEF': 'Creates a new backup plan',
      'DESCRIPTION': """\
          Create a new backup plan in the project. It can only be created in
          locations where Backup and DR is available.
      """,
      'EXAMPLES': """\
        To create a new backup plan ``sample-backup-plan''
        in project ``sample-project'',
        at location ``us-central1'',
        with resource-type ``compute.<UNIVERSE_DOMAIN>.com/Instance''
        with 2 backup-rules:

        run:

          $ {command} sample-backup-plan --project=sample-project --location=us-central1
            --resource-type 'compute.<UNIVERSE_DOMAIN>.com/Instance'
            --backup-rule <BACKUP-RULE>
            --backup-rule <BACKUP-RULE>

        Backup Rule Examples:

        1. Hourly backup rule with hourly backup frequency of 6 hours and store it for 30 days, and expect the backups to run only between 10:00 to 20:00 UTC

        <BACKUP-RULE>: rule-id=sample-hourly-rule,backup-vault=projects/admin-project/locations/us-central1/backupVaults/bv1,retention-days=30,recurrence=HOURLY,hourly-frequency=6,time-zone=UTC,backup-window-start=10,backup-window-end=20

        Properties:
          -- rule-id = "sample-hourly-rule"
          -- backup-vault = projects/admin-project/locations/us-central1/backupVaults/bv1
          -- retention-days = 30
          -- recurrence = HOURLY
          -- hourly-frequency = 6
          -- time-zone = UTC
          -- backup-window-start = 10
          -- backup-window-end = 20

        2. Daily backup rule with daily backup frequency of 6 hours and store it for 7 days

        <BACKUP-RULE>: rule-id=sample-daily-rule,backup-vault=projects/admin-project/locations/us-central1/backupVaults/bv1,retention-days=7,recurrence=DAILY,backup-window-start=1,backup-window-end=14

        Properties:
          -- rule-id = "sample-daily-rule"
          -- backup-vault = projects/admin-project/locations/us-central1/backupVaults/bv1
          -- retention-days = 7
          -- recurrence = DAILY
          -- backup-window-start = 1
          -- backup-window-end = 14

        3. Weekly backup rule with weekly backup frequency on every MONDAY & FRIDAY and store it for 21 days

        <BACKUP-RULE>: rule-id=sample-weekly-rule,backup-vault=projects/admin-project/locations/us-central1/backupVaults/bv1,retention-days=21,recurrence=WEEKLY,days-of-week="MONDAY FRIDAY",backup-window-start=10,backup-window-end=20

        Properties:
          -- rule-id = "sample-weekly-rule"
          -- backup-vault = projects/admin-project/locations/us-central1/backupVaults/bv1
          -- retention-days: 21
          -- recurrence = WEEKLY
          -- days-of-week = "MONDAY FRIDAY"
          -- backup-window-start = 10
          -- backup-window-end = 20
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddBackupPlanResourceArg(
        parser,
        """Name of the backup plan to be created.
        Once the backup plan is created, this name can't be changed.
        The name must be unique for a project and location.
        """,
    )
    flags.AddResourceType(parser)
    flags.AddBackupRule(parser)

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """
    client = BackupPlansClient()
    is_async = args.async_

    backup_plan = args.CONCEPTS.backup_plan.Parse()
    resource_type = args.resource_type
    backup_rules = args.backup_rule

    try:
      operation = client.Create(backup_plan, resource_type, backup_rules)
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT)

    if is_async:
      log.CreatedResource(
          operation.name,
          kind='backup plan',
          is_async=True,
          details=(
              'Creation in progress for backup plan [{}]. Run the [gcloud'
              ' backup-dr operations describe] command to check the status of'
              ' this operation.'.format(backup_plan.RelativeName())
          ),
      )
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'Creating backup plan [{}]. (This operation could'
            ' take upto 2 minutes.)'.format(backup_plan.RelativeName())
        ),
    )
    log.CreatedResource(backup_plan.RelativeName(), kind='backup plan')

    return resource
