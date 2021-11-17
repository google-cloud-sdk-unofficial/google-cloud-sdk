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
"""Command to create a node pool in an Anthos cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import flags as aws_flags
from googlecloudsdk.command_lib.container.aws import node_pools
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.container.gkemulticloud import operations
from googlecloudsdk.core import log

# Command needs to be in one line for the docgen tool to format properly.
_EXAMPLES = """
To create a node pool named ``my-node-pool'' in a cluster named ``my-cluster''
managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1 --iam-instance-profile=IAM_INSTANCE_PROFILE --node-version=NODE_VERSION --subnet-id=SUBNET_ID
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a node pool in an Anthos cluster on AWS."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAwsNodePoolResourceArg(parser, 'to create')
    flags.AddNodeVersion(parser)
    flags.AddSubnetID(parser, 'the node pool')
    flags.AddAutoscaling(parser)
    flags.AddMaxPodsPerNode(parser)
    flags.AddRootVolumeSize(parser)
    flags.AddValidateOnly(parser, 'node pool to create')
    flags.AddTags(parser, 'node pool')
    flags.AddNodeLabels(parser)
    flags.AddNodeTaints(parser)

    aws_flags.AddInstanceType(parser)
    aws_flags.AddSshEC2KeyPair(parser)
    aws_flags.AddIamInstanceProfile(parser)
    aws_flags.AddSecurityGroupIds(parser, 'nodes')
    aws_flags.AddRootVolumeType(parser)
    aws_flags.AddRootVolumeIops(parser)
    aws_flags.AddRootVolumeKmsKeyArn(parser)
    aws_flags.AddProxyConfig(parser)
    aws_flags.AddConfigEncryptionKmsKeyArn(parser)

    base.ASYNC_FLAG.AddToParser(parser)

    parser.display_info.AddFormat(node_pools.NODEPOOLS_FORMAT)

  def Run(self, args):
    """Run the create command."""
    release_track = self.ReleaseTrack()
    node_pool_ref = resource_args.ParseAwsNodePoolResourceArg(args)

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAwsNodePoolResourceArg(args).locationsId,
        release_track):
      # Parsing again after endpoint override is set.
      node_pool_ref = resource_args.ParseAwsNodePoolResourceArg(args)
      node_pool_client = node_pools.NodePoolsClient(track=release_track)
      args.root_volume_size = flags.GetRootVolumeSize(args)
      args.root_volume_type = aws_flags.GetRootVolumeType(args)
      args.node_taints = flags.GetNodeTaints(args)

      op = node_pool_client.Create(node_pool_ref, args)
      op_ref = resource_args.GetOperationResource(op)

      validate_only = getattr(args, 'validate_only', False)
      if validate_only:
        args.format = 'disable'
        return

      log.CreatedResource(op_ref, kind=constants.LRO_KIND)

      async_ = getattr(args, 'async_', False)
      if not async_:
        op_client = operations.Client(track=release_track)
        op_client.Wait(
            op_ref,
            'Creating node pool {}'.format(node_pool_ref.awsNodePoolsId))

      log.CreatedResource(
          node_pool_ref, kind=constants.AWS_NODEPOOL_KIND, is_async=async_)
      return node_pool_client.Get(node_pool_ref)
