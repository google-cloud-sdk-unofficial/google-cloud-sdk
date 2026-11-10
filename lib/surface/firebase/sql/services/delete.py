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
"""Command to delete a Firebase SQL Connect service."""

from googlecloudsdk.api_lib.firebase import sql as sql_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firebase.sql import flags
from googlecloudsdk.core import properties


@base.RegionalEndpointsSupported
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete a Firebase SQL Connect service."""

  detailed_help = {
      'EXAMPLES': (
          """\
          To delete a Firebase SQL Connect service:

            $ {command} my-service --location=us-central1
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    flags.AddServicePositionalArg(parser)
    flags.AddLocationFlag(parser, required=True)
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help=(
            'If set, validate the request, but do not actually delete the'
            ' service.'
        ),
    )

  def Run(self, args):
    project_id = properties.VALUES.core.project.Get(required=True)
    client = sql_util.SqlClient()
    return client.DeleteService(
        project_id=project_id,
        location=args.location,
        service_id=args.service,
        validate_only=args.validate_only,
    )
