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

"""Command to list databases."""


from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
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
  r"""List databases.

  ## DESCRIPTION
    Lists all Databases for the specified location.

  ## EXAMPLES
  To list all databases in the location `us-east4`, run:

      $ {command} --location=us-east4

  To list all databases for a DbSystem with id `my-db-system` in the
  location `us-east4`, run:

      $ {command} --location=us-east4 \
          --filter='dbSystem="projects/my-project/locations/us-east4/dbSystems/my-db-system"'
  """

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser.ForResource(
        '--location',
        util.GetLocationResourceSpec(),
        group_help='The location you want to list the databases for.',
        required=True).AddToParser(parser)

    parser.display_info.AddFormat('table(name.basename():label=NAME)')

    base.FILTER_FLAG.RemoveFromParser(parser)
    base.Argument(
        '--filter',
        metavar='EXPRESSION',
        require_coverage_in_tests=False,
        category=base.LIST_COMMAND_FLAGS,
        help="""\
        Apply a filter in the format :
        --filter='dbSystem="projects/my-project/locations/us-east4/dbSystems/my-db-system"'
        """,
    ).AddToParser(parser)

  def Run(self, args):
    """List databases."""
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

    _, backend_filter = util.GcloudFilterBackend(
        {'dbSystem': 'dbSystem', 'db_system': 'dbSystem'}).Rewrite(args.filter)
    # We clear args.filter to prevent the automatic list command filtering
    # from incorrectly filtering out results based on server-only fields.
    # We will apply the filtering manually below.
    args.filter = None

    results = list_pager.YieldFromList(
        client.projects_locations_databases,
        messages.OracledatabaseProjectsLocationsDatabasesListRequest(
            parent=ref.RelativeName(),
            pageSize=args.page_size,
            filter=backend_filter,
        ),
        batch_size=args.page_size,
        field='databases',
        limit=args.limit,
        batch_size_attribute='pageSize',
    )

    if matcher:
      extra_fields = {
          'dbSystem': util.MatchAnything(),
          'db_system': util.MatchAnything(),
      }
      return (r for r in results
              if matcher.Evaluate(util.ResourceWrapper(r, extra_fields)))
    return results
