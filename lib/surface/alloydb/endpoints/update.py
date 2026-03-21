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
"""Updates an AlloyDB endpoint."""

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import endpoint_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  """Update an AlloyDB endpoint."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To update an endpoint, run:

            $ {command} my-endpoint --region=us-central1 --target-instances=projects/my-project/locations/us-central1/clusters/my-cluster/instances/my-instance-1,projects/my-project/locations/us-central1/clusters/my-cluster/instances/my-instance-2
          """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional parameters for the command.

    Args:
      parser: The command line parser.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddEndpoint(parser)
    flags.AddRegion(parser)
    flags.AddTargetInstances(parser, required=True)

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      Process object for due to --async flag, or a response message indicating
      the result of the update operation.
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

    endpoint = alloydb_messages.Endpoint()
    update_masks = []

    if args.IsSpecified('target_instances'):
      endpoint.targetInstances = args.target_instances
      update_masks.append('target_instances')

    req = alloydb_messages.AlloydbProjectsLocationsEndpointsPatchRequest(
        name=endpoint_ref.RelativeName(),
        endpoint=endpoint,
        updateMask=','.join(update_masks),
    )
    op = alloydb_client.projects_locations_endpoints.Patch(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations'
    )
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      endpoint_operations.Await(
          op_ref, 'Updating endpoint', self.ReleaseTrack()
      )
    return op
