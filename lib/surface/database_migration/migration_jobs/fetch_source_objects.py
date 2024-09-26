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
"""Command to restart migration jobs for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.api_lib.database_migration import migration_jobs
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration.migration_jobs import flags as mj_flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
        Fetch objects for a Database Migration Service migration job by connection to the source.
        """,
    'EXAMPLES': """\
        To fetch source objects for a migration job:

          $ {command} MIGRATION_JOB --region=us-central1
        """,
}


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class FetchSourceObjects(base.Command):
  """Fetch objects for a Database Migration Service migration job by connection to the source."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddOnlyMigrationJobResourceArgs(parser, 'to restart')
    mj_flags.AddNoAsyncFlag(parser)

  def Run(self, args):
    """Fetch source objects for a Database Migration Service migration job.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the restart
      operation if the restart was successful.
    """
    migration_job_ref = args.CONCEPTS.migration_job.Parse()

    mj_client = migration_jobs.MigrationJobsClient(self.ReleaseTrack())
    result_operation = mj_client.FetchSourceObjects(
        migration_job_ref.RelativeName(),
    )

    client = api_util.GetClientInstance(self.ReleaseTrack())
    messages = api_util.GetMessagesModule(self.ReleaseTrack())
    resource_parser = api_util.GetResourceParser(self.ReleaseTrack())

    if args.IsKnownAndSpecified('no_async'):
      log.status.Print(
          'Waiting for migration job [{}] to fetch source objects with [{}]'
          .format(migration_job_ref.migrationJobsId, result_operation.name)
      )

      api_util.HandleLRO(
          client,
          result_operation,
          client.projects_locations_migrationJobs,
          no_resource=True,
      )

      operation_ref = resource_parser.Create(
          'datamigration.projects.locations.operations',
          operationsId=result_operation.name,
          projectsId=migration_job_ref.projectsId,
          locationsId=migration_job_ref.locationsId,
      )

      operation_response = client.projects_locations_operations.Get(
          messages.DatamigrationProjectsLocationsOperationsGetRequest(
              name=operation_ref.operationsId
          )
      )

      log.status.Print(
          'Fetched source objects for migration job {} [{}]'.format(
              migration_job_ref.migrationJobsId, result_operation.name
          )
      )
      response_dict = encoding.MessageToPyValue(operation_response.response)

      for objects in response_dict['sourceObjects']:
        log.status.Print(objects)

      return

    operation_ref = resource_parser.Create(
        'datamigration.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=migration_job_ref.projectsId,
        locationsId=migration_job_ref.locationsId,
    )

    return client.projects_locations_operations.Get(
        messages.DatamigrationProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId
        )
    )
