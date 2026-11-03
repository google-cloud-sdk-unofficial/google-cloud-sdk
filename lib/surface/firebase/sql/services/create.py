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
"""Command to create a Firebase SQL Connect service."""

from googlecloudsdk.api_lib.firebase import sql as sql_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firebase.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.RegionalEndpointsSupported
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a new Firebase SQL Connect service."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Create a new Firebase SQL Connect service.

          By default, when `--cloud-sql-instance-id` and
          `--cloud-sql-database-id` are omitted, a new underlying Cloud SQL
          instance and database with the same ID as `SERVICE` will be created.
          Passing `--cloud-sql-instance-id` and `--cloud-sql-database-id` links
          the new service to an existing Cloud SQL instance and database (or
          creates them if they do not exist).
      """
      ),
      'EXAMPLES': (
          """\
          To create a service with a new default Cloud SQL instance and database:

            $ {command} my-service --location=us-central1

          To create a service linked to an existing Cloud SQL instance and database:

            $ {command} my-service --location=us-central1 --cloud-sql-instance-id=my-sql-instance --cloud-sql-database-id=my-db

          To create a service with initial SQL migrations:

            $ {command} my-service --location=us-central1 --sql-source-dir=./sql
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    flags.AddServicePositionalArg(parser)
    flags.AddLocationFlag(parser, required=True)
    cloud_sql_group = parser.add_group(
        help=(
            'Cloud SQL instance and database configuration. If omitted, both'
            ' default to the service ID and a new Cloud SQL instance and'
            ' database will be created.'
        ),
    )
    cloud_sql_group.add_argument(
        '--cloud-sql-instance-id',
        required=True,
        help=(
            'Cloud SQL instance ID or resource name to link to the service, or'
            ' to create if it does not exist.'
        ),
    )
    cloud_sql_group.add_argument(
        '--cloud-sql-database-id',
        required=True,
        help=(
            'Cloud SQL database ID to link to the service, or to create if it'
            ' does not exist.'
        ),
    )
    parser.add_argument(
        '--sql-source-dir',
        help='Path to a local directory containing SQL migration files.',
    )

  def Run(self, args):
    service_id = args.service

    project_id = properties.VALUES.core.project.Get(required=True)
    client = sql_util.SqlClient()
    response = client.CreateService(
        service_id=service_id,
        location=args.location,
        project_id=project_id,
        cloud_sql_instance=args.cloud_sql_instance_id,
        cloud_sql_database=args.cloud_sql_database_id,
        sql_source_dir=args.sql_source_dir,
    )
    log.CreatedResource(service_id, kind='service')
    return response
