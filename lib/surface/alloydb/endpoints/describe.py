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
"""Describes an AlloyDB endpoint."""

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA
)
@base.Hidden
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Describe an AlloyDB endpoint in a given project and region."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To describe an endpoint, run:

            $ {command} my-endpoint --region=us-central1
          """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    flags.AddRegion(parser)
    flags.AddEndpoint(parser)

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """
    client = api_util.AlloyDBClient(self.ReleaseTrack())
    alloydb_client = client.alloydb_client
    alloydb_messages = client.alloydb_messages
    endpoint_ref = client.resource_parser.Create(
        'alloydb.projects.locations.endpoints',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region,
        endpointsId=args.endpoint,
    )
    req = alloydb_messages.AlloydbProjectsLocationsEndpointsGetRequest(
        name=endpoint_ref.RelativeName()
    )
    return alloydb_client.projects_locations_endpoints.Get(req)
