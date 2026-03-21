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
"""Creates a new AlloyDB endpoint."""

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import endpoint_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import endpoint_helper
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA
)
@base.Hidden
@base.DefaultUniverseOnly
class Create(base.CreateCommand):
  """Creates a new AlloyDB endpoint."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To create a new write endpoint for an instance, run:

            $ {command} my-endpoint --region=us-central1 --endpoint-type=WRITE_ENDPOINT --target-instances=projects/my-project/locations/us-central1/clusters/my-cluster/instances/my-instance
          """
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs
    """
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddEndpoint(parser)
    flags.AddRegion(parser)
    flags.AddTargetInstances(parser)
    flags.AddEndpointType(parser)

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
    location_ref = client.resource_parser.Create(
        'alloydb.projects.locations',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region,
    )

    req = endpoint_helper.ConstructCreateRequestFromArgs(
        alloydb_messages, location_ref, args
    )
    op = alloydb_client.projects_locations_endpoints.Create(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations'
    )
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      endpoint_operations.Await(
          op_ref, 'Creating endpoint', self.ReleaseTrack()
      )
    return op
