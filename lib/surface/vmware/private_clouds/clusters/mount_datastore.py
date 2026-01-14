# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""'vmware clusters mount-datastore' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.vmware import clusters
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

ClustersClient = clusters.ClustersClient
DETAILED_HELP = {
    'DESCRIPTION': """
          Mount a datastore to a cluster in a VMware Engine private cloud.
        """,
    'EXAMPLES': """
          To mount a datastore `my-datastore` to cluster `my-cluster` in private cloud `my-private-cloud` in zone `us-west2-a`, providing subnet, run:

            $ {command} my-cluster --location=us-west2-a --project=my-project --private-cloud=my-private-cloud --datastore=projects/my-project/locations/us-west2-a/datastores/my-datastore --subnet=my-subnet

            Or:

            $ {command} my-cluster --private-cloud=my-private-cloud --datastore=projects/my-project/locations/us-west2-a/datastores/my-datastore --subnet=my-subnet

          To mount a datastore `my-datastore` to cluster `my-cluster` in private cloud `my-private-cloud` in zone `us-west2-a`, providing a json file for datastore network, run:

            $ {command} my-cluster --location=us-west2-a --project=my-project --private-cloud=my-private-cloud --datastore=projects/my-project/locations/us-west2-a/datastores/my-datastore --datastore-network=network-config.json

            Where `network-config.json` contains:
            {
              "subnet": "my-subnet",
              "mtu": 1500,
              "connection-count": 4
            }

            In the examples without location and project, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class MountDatastore(base.UpdateCommand):
  """Mount a datastore to a Google Cloud VMware Engine cluster."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddClusterArgToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--datastore',
        required=True,
        help='The datastore resource name to mount.',
    )
    network_group = parser.add_mutually_exclusive_group(required=True)
    inlined_network_group = network_group.add_argument_group(
        help='Datastore network configuration if not providing via file.'
    )
    inlined_network_group.add_argument(
        '--subnet',
        required=True,
        help="""Subnet to use for inlined datastore network configuration.""",
    )
    inlined_network_group.add_argument(
        '--mtu',
        type=int,
        help="""MTU for inlined datastore network configuration.""",
    )
    inlined_network_group.add_argument(
        '--connection-count',
        type=int,
        help="""Connection count for inlined datastore network configuration.""",
    )
    network_group.add_argument(
        '--datastore-network',
        type=arg_parsers.FileContents(),
        help="""Path to a JSON file containing the datastore network configuration.""",
    )
    parser.add_argument(
        '--access-mode',
        choices=['READ_WRITE', 'READ_ONLY'],
        help="""Access mode for the datastore.""",
    )
    parser.add_argument(
        '--nfs-version',
        choices=['NFS_V3', 'NFS_V4'],
        help="""NFS version for the datastore.""",
    )
    parser.add_argument(
        '--ignore-colocation',
        action='store_true',
        help="""If set, ignore colocation checks.""",
    )

  def Run(self, args):
    cluster = args.CONCEPTS.cluster.Parse()
    client = ClustersClient()
    is_async = args.async_
    subnet = args.subnet
    mtu = args.mtu
    connection_count = args.connection_count
    if args.datastore_network:
      try:
        datastore_network_config = json.loads(args.datastore_network)
        subnet = datastore_network_config.get('subnet')
        mtu = datastore_network_config.get('mtu')
        connection_count = datastore_network_config.get('connection-count')
      except ValueError as e:
        raise ValueError(
            'Invalid JSON format for datastore-network file: ' + str(e)
        )
    operation = client.MountDatastore(
        cluster_ref=cluster,
        datastore=args.datastore,
        subnet=subnet,
        mtu=mtu,
        connection_count=connection_count,
        access_mode=args.access_mode,
        nfs_version=args.nfs_version,
        ignore_colocation=args.ignore_colocation,
    )

    if is_async:
      log.UpdatedResource(
          operation.name,
          kind=f'cluster {cluster.RelativeName()}',
          is_async=True,
      )
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=f'waiting for cluster [{cluster.RelativeName()}] to be updated',
    )
    log.UpdatedResource(
        cluster.RelativeName(),
        kind='cluster',
        details=f'datastore [{args.datastore}] mounted',
    )
    return resource
