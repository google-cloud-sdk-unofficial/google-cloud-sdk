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
"""Command to list Grid Infrastructure versions."""


from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.oracle_database import filter_rewrite
from googlecloudsdk.command_lib.oracle_database import util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_transform

VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha',
    base.ReleaseTrack.GA: 'v1',
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  r"""List Grid Infrastructure versions.

  ## DESCRIPTION
    Lists all Grid Infrastructure versions for the specified location.

  ## EXAMPLES
  To list all Grid Infrastructure versions in the location `us-east4`, run:

      $ {command} --location=us-east4

  To list a specific Grid Infrastructure version in the location `us-east4`, run:

      $ {command} --location=us-east4 \
          --filter='gi_version="19.0.0.0"'
  """

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser.ForResource(
        '--location',
        util.GetLocationResourceSpec(),
        group_help='The location you want to list the Grid Infrastructure '
        'versions for.',
        required=True).AddToParser(parser)

    # The standard FILTER_FLAG is added by base.ListCommand.

    parser.display_info.AddFormat('table(version:label=NAME)')

    base.FILTER_FLAG.RemoveFromParser(parser)
    base.Argument(
        '--filter',
        metavar='EXPRESSION',
        require_coverage_in_tests=False,
        category=base.LIST_COMMAND_FLAGS,
        help="""\
        Apply a filter in the format :
        --filter='gi_version="19.0.0.0"'
        """,
    ).AddToParser(parser)

  def Run(self, args):
    """List Grid Infrastructure versions."""
    client = apis.GetClientInstance(
        'oracledatabase', VERSION_MAP[self.ReleaseTrack()])
    messages = apis.GetMessagesModule(
        'oracledatabase', VERSION_MAP[self.ReleaseTrack()])
    ref = args.CONCEPTS.location.Parse()
    matcher = None
    if args.filter:
      matcher = resource_filter.Compile(
          args.filter,
          defaults=resource_projection_spec.ProjectionSpec(
              symbols=resource_transform.GetTransforms()
          ),
      )

    _, server_filter = filter_rewrite.GiVersionBackend().Rewrite(args.filter)
    # We clear args.filter to prevent the automatic list command filtering
    # from incorrectly filtering out results based on server-only fields.
    # We will apply the filtering manually below.
    args.filter = None

    results = list_pager.YieldFromList(
        client.projects_locations_giVersions,
        messages.OracledatabaseProjectsLocationsGiVersionsListRequest(
            parent=ref.RelativeName(),
            pageSize=args.page_size,
            filter=server_filter,
        ),
        batch_size=args.page_size,
        field='giVersions',
        limit=args.limit,
        batch_size_attribute='pageSize',
    )

    if matcher:
      extra_fields = {
          'shape': filter_rewrite.MatchAnything(),
          'gcp_oracle_zone': filter_rewrite.MatchAnything(),
          'gi_version': filter_rewrite.MatchAnything(),
      }
      return (r for r in results
              if matcher.Evaluate(filter_rewrite.ResourceWrapper(r, extra_fields)))
    return results
