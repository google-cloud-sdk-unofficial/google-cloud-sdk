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
"""Command to fetch issues for a database migration conversion workspace."""

import argparse
from typing import Any, Iterator

from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration.conversion_workspaces import command_mixin
from googlecloudsdk.command_lib.database_migration.conversion_workspaces import flags as cw_flags

_DEFAULT_PAGE_SIZE = 100


@base.RegionalEndpointsSupported
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class FetchIssues(
    command_mixin.ConversionWorkspacesCommandMixin,
    base.ListCommand,
):
  """Fetch issues in a Database Migration conversion workspace."""

  detailed_help = {
      'DESCRIPTION': (
          """
        Fetch issues in a Database Migration conversion workspace.
      """
      ),
      'EXAMPLES': (
          """\
        To fetch the issues in a conversion workspace
        in a project and location `us-central1`, run:

            $ {command} my-conversion-workspace --region=us-central1
      """
      ),
  }

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    resource_args.AddConversionWorkspaceResourceArg(parser, 'fetch issues')
    cw_flags.AddAllIssuesFlag(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, _DEFAULT_PAGE_SIZE)

    parser.display_info.AddFormat("""
          table(
            entityFullName:label=ENTITY_NAME,
            entityType:label=ENTITY_TYPE,
            severity:label=SEVERITY,
            type:label=TYPE,
            message:label=MESSAGE,
            issueOrigin:label=ORIGIN,
            issueState:label=STATE
          )
        """)

  def Run(
      self,
      args: argparse.Namespace,
  ) -> Iterator[dict[str, Any]]:
    """Fetch issues for a DMS conversion workspace.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      An iterator of issues for the specified conversion workspace and
      arguments.
    """
    conversion_workspace_ref = args.CONCEPTS.conversion_workspace.Parse()
    client = self.GetClient(location=conversion_workspace_ref.locationsId)
    return client.entities.FetchIssues(
        name=conversion_workspace_ref.RelativeName(),
        all_issues=args.all_issues,
        filter_expr=self.ExtractBackendFilter(args),
        page_size=args.GetValue('page_size'),
    )
