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
"""Command to create a new GKE node pool on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import flags as aws_flags
from googlecloudsdk.command_lib.container.aws import node_pools
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a GKE node pool on AWS."""

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

    aws_flags.AddInstanceType(parser)
    aws_flags.AddSshEC2KeyPair(parser)
    aws_flags.AddIamInstanceProfile(parser)
    aws_flags.AddSecurityGroupIds(parser, 'nodes')

    base.ASYNC_FLAG.AddToParser(parser)

    parser.display_info.AddFormat(node_pools.NODEPOOLS_FORMAT)

  def Run(self, args):
    """Run the create command."""
    release_track = self.ReleaseTrack()
    node_pool_ref = args.CONCEPTS.node_pool.Parse()

    with endpoint_util.GkemulticloudEndpointOverride(node_pool_ref.locationsId,
                                                     release_track):
      node_pool_client = node_pools.NodePoolsClient(track=release_track)
      args.root_volume_size = flags.GetRootVolumeSize(args)
      args.main_volume_size = flags.GetMainVolumeSize(args)
      op = node_pool_client.Create(node_pool_ref, args)
      op_ref = resource_args.GetOperationResource(op)

      validate_only = getattr(args, 'validate_only', False)
      if validate_only:
        args.format = 'disable'
        return

      async_ = getattr(args, 'async_', False)
      if not async_:
        waiter.WaitFor(
            waiter.CloudOperationPollerNoResources(
                node_pool_client.client.projects_locations_operations),
            op_ref,
            'Creating node pool {}'.format(node_pool_ref.awsNodePoolsId),
            wait_ceiling_ms=constants.MAX_LRO_POLL_INTERVAL_MS)

      log.CreatedResource(node_pool_ref)
      return node_pool_client.Get(node_pool_ref)
