# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Creates a new AlloyDB instance."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import instance_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.command_lib.alloydb import instance_helper
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Creates a new AlloyDB instance within a given cluster."""

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs
    """
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddAssignIp(parser)
    flags.AddAvailabilityType(parser)
    flags.AddCPU(parser)
    flags.AddCluster(parser, False)
    flags.AddDatabaseFlags(parser)
    flags.AddInstance(parser)
    flags.AddInstanceType(parser)
    flags.AddMemory(parser)
    flags.AddReadPoolSize(parser)
    flags.AddRegion(parser)
    flags.AddTier(parser)
    flags.AddZone(parser)
    # TODO(b/185795425): Add --ssl-required and --labels later once we
    # understand the use cases

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
          arguments specified in the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """
    client = api_util.AlloyDBClient(api_util.API_VERSION_DEFAULT)
    alloydb_client = client.alloydb_client
    alloydb_messages = client.alloydb_messages
    cluster_ref = client.resource_parser.Create(
        'alloydb.projects.locations.clusters',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region,
        clustersId=args.cluster)
    req = instance_helper.ConstructCreateRequestFromArgs(
        client, alloydb_messages, cluster_ref, args)
    op = alloydb_client.projects_locations_clusters_instances.Create(req)
    if not args.async_:
      instance_operations.Await(op, 'Creating instance')
    return op
