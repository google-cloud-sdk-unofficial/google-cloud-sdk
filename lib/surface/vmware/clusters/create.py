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
"""'vmware clusters create' command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.vmware.clusters import ClustersClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Google Cloud VMware Engine cluster."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddClusterArgToParser(parser, positional=True)
    flags.AddNodeTypeArgToParser(parser)
    parser.add_argument(
        '--node-count',
        required=True,
        type=int,
        help="""\
        Nodes count for cluster
        """)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    cluster = args.CONCEPTS.cluster.Parse()
    client = ClustersClient()
    operation = client.Create(cluster, args.node_type,
                              args.node_count)
    log.CreatedResource(operation.name, kind='cluster', is_async=True)

Create.detailed_help = {
    'DESCRIPTION':
        """
          Create a cluster in a VMware Engine private cloud. Successful creation of a cluster results in a cluster in READY state. Check the progress of a cluster using `gcloud alpha vmware clusters list`.
        """,
    'EXAMPLES':
        """
          To create a cluster called ``my-cluster'' in private cloud ``my-privatecloud'', with 3 initial ``standard-72'' nodes in zone ``us-west2-a'', run:

            $ {command} my-cluster --location=us-west2-a --project=my-project --privatecloud=my-privatecloud --node-type=standard-72 --node-count=3
            Or:

            $ {command} my-cluster --privatecloud=my-privatecloud --node-type=standard-72 --node-count=3
            In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}
