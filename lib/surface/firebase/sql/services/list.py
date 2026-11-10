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
"""Command to list Firebase SQL Connect services."""

from googlecloudsdk.api_lib.firebase import sql as sql_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firebase.sql import flags
from googlecloudsdk.core import properties


@base.RegionalEndpointsSupported
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Firebase SQL Connect services in a project."""

  detailed_help = {
      'EXAMPLES': (
          """\
          To list all Firebase SQL Connect services in the current project across all locations:

            $ {command}

          To list all Firebase SQL Connect services in `us-central1`:

            $ {command} --location=us-central1
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    flags.AddLocationFlag(parser, required=False)

  def Run(self, args):
    project_id = properties.VALUES.core.project.Get(required=True)
    client = sql_util.SqlClient()
    return client.ListServices(
        project_id=project_id,
        location=args.location,
        page_size=args.page_size,
    )
