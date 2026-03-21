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
"""Deletes an AlloyDB endpoint."""

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import endpoint_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@base.Hidden
class Delete(base.DeleteCommand):
  """Deletes an AlloyDB endpoint."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To delete an endpoint, run:

            $ {command} my-endpoint --region=us-central1
          """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional parameters for the command.

    Args:
      parser: The command line parser.
    """
    flags.AddRegion(parser)
    flags.AddEndpoint(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      Process object for due to --async flag, or a response message indicating
      the result of the delete operation.
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
    prompt_message = (
        'The endpoint will be deleted upon completion.'
    )
    if not console_io.PromptContinue(message=prompt_message):
      return None

    req = alloydb_messages.AlloydbProjectsLocationsEndpointsDeleteRequest(
        name=endpoint_ref.RelativeName()
    )
    op = alloydb_client.projects_locations_endpoints.Delete(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations'
    )
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      endpoint_operations.Await(
          op_ref, 'Deleting endpoint', self.ReleaseTrack(), False
      )
    return op
