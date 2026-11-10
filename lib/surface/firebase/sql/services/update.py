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
"""Command to update a Firebase SQL Connect service."""

from googlecloudsdk.api_lib.firebase import sql as sql_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firebase.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.RegionalEndpointsSupported
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a Firebase SQL Connect service."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Update a Firebase SQL Connect service's metadata and/or apply SQL
          migrations.
      """
      ),
      'EXAMPLES': (
          """\
          To update the display name and labels of a service:

            $ {command} my-service --location=us-central1 --display-name="My Service" --labels=env=prod,team=firesql

          To apply SQL migrations from a local SQL source directory:

            $ {command} my-service --location=us-central1 --sql-source-dir=./sql

          To validate a service update without applying changes:

            $ {command} my-service --location=us-central1 --sql-source-dir=./sql --validate-only
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    flags.AddServicePositionalArg(parser)
    flags.AddLocationFlag(parser, required=True)
    parser.add_argument(
        '--annotations',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(),
        help='List of annotation KEY=VALUE pairs to set on the service.',
    )
    parser.add_argument(
        '--display-name',
        help=(
            'Mutable human-readable display name for the service (63 character'
            ' limit).'
        ),
    )
    parser.add_argument(
        '--labels',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(),
        help='List of label KEY=VALUE pairs to set on the service.',
    )
    parser.add_argument(
        '--sql-source-dir',
        help='Path to a local directory containing SQL migration files.',
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help=(
            'If set, validate the request, but do not actually update the'
            ' service.'
        ),
    )

  def Run(self, args):
    service_id = args.service
    project_id = properties.VALUES.core.project.Get(required=True)
    client = sql_util.SqlClient()
    response = client.UpdateService(
        project_id=project_id,
        location=args.location,
        service_id=service_id,
        display_name=args.display_name,
        labels=args.labels,
        annotations=args.annotations,
        sql_source_dir=args.sql_source_dir,
        validate_only=args.validate_only,
    )
    if args.validate_only:
      log.status.Print('Validation complete.')
    else:
      log.UpdatedResource(service_id, kind='service')
    return response
