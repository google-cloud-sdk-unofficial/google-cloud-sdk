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
"""Command to convert conversion workspaces for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import conversion_workspaces
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration.conversion_workspaces import flags as cw_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers

DETAILED_HELP = {
    'DESCRIPTION': """
        Convert the provided source code from accessing the source database to
        accessing the destination database.
        """,
    'EXAMPLES': """\
        To convert the application code:

            $ {command} --source-file=Path/to/source --region=us-central1
        """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class ConvertApplicationCode(base.Command):
  """Convert the application code."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    concept_parsers.ConceptParser.ForResource(
        '--region',
        resource_args.GetRegionResourceSpec(),
        group_help='The location of the resource.',
        required=True,
    ).AddToParser(parser)
    cw_flags.AddSourceDetailsFlag(parser)
    cw_flags.AddTargetPathFlag(parser)

  def Run(self, args):
    """Convert the application code.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      None.
    """
    region_ref = args.CONCEPTS.region.Parse()
    cw_client = conversion_workspaces.ConversionWorkspacesClient(
        self.ReleaseTrack()
    )
    return cw_client.ConvertApplicationCode(region_ref.RelativeName(), args)
