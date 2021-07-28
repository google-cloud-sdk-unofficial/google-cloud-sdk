# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""'vmware privateclouds create' command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a VMware Engine private cloud. Private cloud creation is considered finished when the private cloud is in READY state. Check the progress of a private cloud using `gcloud alpha vmware privateclouds list`.
        """,
    'EXAMPLES':
        """
          To create a private cloud in the ``us-west2-a'' zone using ``standard-72'' nodes that connects to the ``default-vpc'' VPC network of another project, run:


          $ {command} my-privatecloud --location=us-west2-a --project=my-project --cluster=my-management-cluster --node-type=standard-72 --node-count=3 --management-range=192.168.0.0/24 --network=default-vpc --network-project=another-project

          Or:

          $ {command} my-privatecloud --cluster=my-management-cluster--node-type=standard-72 --node-count=3 --management-range=192.168.0.0/24 --network=default-vpc --network-project=another-project

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a VMware Engine private cloud."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=True)
    flags.AddClusterArgToParser(parser, positional=False)
    flags.AddNodeTypeArgToParser(parser)
    parser.add_argument(
        '--description',
        help="""\
        Text describing the private cloud
        """)
    parser.add_argument(
        '--node-count',
        required=True,
        type=int,
        help="""\
        Node type to use for management cluster nodes. To get a list of available node types, run `gcloud alpha vmware nodetypes list`.
        """)
    parser.add_argument(
        '--management-range',
        required=True,
        help="""\
         IP address range in the private cloud to use for management appliances, in CIDR format. Use an IP address range that meets the [VMware Engine networking requirements](https://cloud.google.com/vmware-engine/docs/quickstart-networking-requirements).
        """)
    parser.add_argument(
        '--network',
        required=True,
        help="""\
        Network ID of the Google Cloud VPC network to connect with your private cloud.
        """)
    parser.add_argument(
        '--network-project',
        required=False,
        help="""\
         Project ID or project name of the VPC network. Use this flag when the VPC network is in another project.
        """)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    privatecloud = args.CONCEPTS.privatecloud.Parse()
    client = PrivateCloudsClient()
    operation = client.Create(privatecloud, args.labels, args.description,
                              args.cluster, args.node_type, args.node_count,
                              args.management_range, args.network,
                              args.network_project)
    log.CreatedResource(operation.name, kind='private cloud', is_async=True)

Create.detailed_help = DETAILED_HELP
