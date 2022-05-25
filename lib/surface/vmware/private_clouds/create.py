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
"""'vmware private-clouds create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a VMware Engine private cloud. Private cloud creation is considered finished when the private cloud is in READY state. Check the progress of a private cloud using `{parent_command} list`.
        """,
    'EXAMPLES':
        """
          To create a private cloud in the ``us-west2-a'' zone using ``standard-72'' nodes that connects to the ``default-vpc'' VPC network of another project, run:


          $ {command} my-private-cloud --location=us-west2-a --project=my-project --cluster=my-management-cluster --node-type=standard-72 --node-count=3 --management-range=192.168.0.0/24 --network=default-vpc --network-project=another-project

          Or:

          $ {command} my-private-cloud --cluster=my-management-cluster --node-type=standard-72 --node-count=3 --management-range=192.168.0.0/24 --network=default-vpc --network-project=another-project

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create a VMware Engine private cloud."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=True)
    flags.AddClusterArgToParser(parser, positional=False)
    flags.AddNodeTypeArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.add_argument(
        '--description',
        help="""\
        Text describing the private cloud.
        """)
    parser.add_argument(
        '--node-count',
        required=True,
        type=int,
        help="""\
        Number of nodes in the management cluster.
        """)
    parser.add_argument(
        '--management-range',
        required=True,
        help="""\
         IP address range in the private cloud to use for management appliances, in CIDR format. Use an IP address range that meets the [VMware Engine networking requirements](https://cloud.google.com/vmware-engine/docs/quickstart-networking-requirements).
        """)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--network',
        required=False,
        help="""\
        Network ID of the Google Cloud VPC network to connect with your private cloud.
        """)
    group.add_argument(
        '--vmware-engine-network',
        required=False,
        hidden=True,
        help="""\
        Network ID of the VMware Engine network attached to the private cloud.
        """)
    parser.add_argument(
        '--network-project',
        required=False,
        help="""\
         Project ID or project name of the VPC network. Use this flag when the VPC network is in another project.
        """)
    parser.add_argument(
        '--node-custom-core-count',
        required=False,
        hidden=True,
        type=int,
        help="""\
         Customized number of virtual cores to use for each node of the management cluster. To get a list of valid values for your node type, run the `{grandparent_command} node-types describe` command and reference the `availableCustomCoreCounts` field in the output.
        """)

  def Run(self, args):
    privatecloud = args.CONCEPTS.private_cloud.Parse()
    client = PrivateCloudsClient()
    is_async = args.async_
    operation = client.Create(privatecloud, args.description,
                              args.cluster, args.node_type, args.node_count,
                              args.management_range, args.network,
                              args.vmware_engine_network, args.network_project,
                              args.node_custom_core_count)
    if is_async:
      log.CreatedResource(operation.name, kind='private cloud', is_async=True)
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for private cloud [{}] to be created'.format(
            privatecloud.RelativeName()))
    log.CreatedResource(resource, kind='private cloud')

    return resource


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a VMware Engine private cloud."""
  _is_hidden = False
