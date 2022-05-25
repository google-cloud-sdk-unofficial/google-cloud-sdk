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
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a cluster in a VMware Engine private cloud. Successful creation of a cluster results in a cluster in READY state. Check the progress of a cluster using `{parent_command} list`.
        """,
    'EXAMPLES':
        """
          To create a cluster called ``my-cluster'' in private cloud ``my-private-cloud'', with 3 initial ``standard-72'' nodes in zone ``us-west2-a'', run:

            $ {command} my-cluster --location=us-west2-a --project=my-project --private-cloud=my-private-cloud --node-type=standard-72 --node-count=3

            Or:

            $ {command} my-cluster --private-cloud=my-private-cloud --node-type=standard-72 --node-count=3

            In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create a Google Cloud VMware Engine cluster."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddClusterArgToParser(parser, positional=True)
    flags.AddNodeTypeArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.add_argument(
        '--node-count',
        required=True,
        type=int,
        help="""\
        Nodes count for cluster
        """)
    parser.add_argument(
        '--node-custom-core-count',
        required=False,
        type=int,
        hidden=True,
        help="""\
         Customized number of virtual cores to use for each node of the cluster. To get a list of valid values for your node type, run the `{grandparent_command} node-types describe` command and reference the `availableCustomCoreCounts` field in the output.
        """)

  def Run(self, args):
    cluster = args.CONCEPTS.cluster.Parse()
    client = ClustersClient()
    is_async = args.async_
    operation = client.Create(cluster, args.node_type,
                              args.node_count, args.node_custom_core_count)
    if is_async:
      log.CreatedResource(operation.name, kind='cluster', is_async=True)
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for cluster [{}] to be created'.format(
            cluster.RelativeName()))
    log.CreatedResource(resource, kind='cluster')

    return resource


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a Google Cloud VMware Engine cluster."""
  _is_hidden = False
