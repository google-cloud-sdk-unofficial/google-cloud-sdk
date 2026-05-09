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

"""Command to list minor versions."""


from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.oracle_database import util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_transform

VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha',
    base.ReleaseTrack.GA: 'v1',
}


def GiVersionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='gi-version', help_text='The GI version ID for the {resource}.')


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='The Cloud location for the {resource}.')


def GetGiVersionResourceSpec(resource_name='gi-version'):
  return concepts.ResourceSpec(
      'oracledatabase.projects.locations.giVersions',
      resource_name=resource_name,
      giVersionsId=GiVersionAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=True)





@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  r"""List minor versions.

  ## DESCRIPTION
    Lists all minor versions for the specified Grid Infrastructure version and
    location.

  ## EXAMPLES
  To list all minor versions for a Grid Infrastructure version with ID `19.0.0.0`
  in the location `us-east4`, run:

      $ {command} --gi-version=19.0.0.0 --location=us-east4

  To list all minor versions for a given shape family with ID `EXADATA.X9M`
  in the location `us-east4` and Grid Infrastructure version with ID `19.0.0.0`,
  run:

      $ {command} --gi-version=19.0.0.0 --location=us-east4 \
          --filter='shape_family="EXADATA.X9M"'
  """

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser.ForResource(
        '--gi-version',
        GetGiVersionResourceSpec(),
        group_help='The GI version you want to list the minor versions for.',
        required=True).AddToParser(parser)

    parser.display_info.AddFormat('table(name.basename():label=NAME)')

    base.FILTER_FLAG.RemoveFromParser(parser)
    base.Argument(
        '--filter',
        metavar='EXPRESSION',
        require_coverage_in_tests=False,
        category=base.LIST_COMMAND_FLAGS,
        help="""\
        Apply a filter in the format:
        --filter='shape_family="EXADATA.X9M"'
        """,
    ).AddToParser(parser)

  def Run(self, args):
    """List minor versions."""
    client = apis.GetClientInstance(
        'oracledatabase', VERSION_MAP[self.ReleaseTrack()])
    messages = apis.GetMessagesModule(
        'oracledatabase', VERSION_MAP[self.ReleaseTrack()])
    ref = args.CONCEPTS.gi_version.Parse()
    matcher = None
    if args.filter:
      matcher = resource_filter.Compile(
          args.filter,
          defaults=resource_projection_spec.ProjectionSpec(
              symbols=resource_transform.GetTransforms()
          ),
      )

    _, backend_filter = util.GcloudFilterBackend({
        'shapeFamily': 'shapeFamily',
        'shape_family': 'shapeFamily',
        'gcp_oracle_zone_id': 'gcp_oracle_zone_id',
    }).Rewrite(args.filter)
    # We clear args.filter to prevent the automatic list command filtering
    # from incorrectly filtering out results based on server-only fields.
    # We will apply the filtering manually below.
    args.filter = None

    results = list_pager.YieldFromList(
        client.projects_locations_giVersions_minorVersions,
        messages.OracledatabaseProjectsLocationsGiVersionsMinorVersionsListRequest(
            parent=ref.RelativeName(),
            pageSize=args.page_size,
            filter=backend_filter,
        ),
        batch_size=args.page_size,
        field='minorVersions',
        limit=args.limit,
        batch_size_attribute='pageSize',
    )

    if matcher:
      extra_fields = {
          'shapeFamily': util.MatchAnything(),
          'shape_family': util.MatchAnything(),
          'gcp_oracle_zone_id': util.MatchAnything(),
      }
      return (r for r in results
              if matcher.Evaluate(util.ResourceWrapper(r, extra_fields)))
    return results
