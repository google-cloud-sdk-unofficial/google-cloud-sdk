# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Restores an AlloyDB cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import cluster_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Restore(base.RestoreCommand):
  """Restores an AlloyDB cluster from a given backup."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To restore a cluster from a backup, run:

          $ {command} my-cluster --region=us-central1 --backup=my-backup
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddCluster(parser)
    flags.AddBackup(parser, False)
    flags.AddRegion(parser)
    flags.AddNetwork(parser)

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
        locationsId=args.region)
    backup_ref = client.resource_parser.Create(
        'alloydb.projects.locations.backups',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region,
        backupsId=args.backup)

    cluster_resource = alloydb_messages.Cluster()
    cluster_resource.network = args.network
    req = alloydb_messages.AlloydbProjectsLocationsClustersRestoreRequest(
        parent=location_ref.RelativeName(),
        restoreClusterRequest=alloydb_messages.RestoreClusterRequest(
            backupSource=alloydb_messages.BackupSource(
                backupName=backup_ref.RelativeName()),
            clusterId=args.cluster,
            cluster=cluster_resource,
        ))
    op = alloydb_client.projects_locations_clusters.Restore(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations')
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      cluster_operations.Await(op_ref, 'Restoring cluster', self.ReleaseTrack())
    return op
