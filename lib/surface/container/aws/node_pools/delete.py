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
"""Command to delete a GKE cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import util as gke_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import node_pools
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete GKE node pool on AWS."""

  @staticmethod
  def Args(parser):
    resource_args.AddAwsNodePoolResourceArg(parser, 'to delete')

    flags.AddValidateOnly(parser, 'node pool to delete')

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    release_track = self.ReleaseTrack()
    node_pool_ref = args.CONCEPTS.node_pool.Parse()

    validate_only = getattr(args, 'validate_only', False)
    if not validate_only:
      console_io.PromptContinue(
          message=gke_util.ConstructList(
              'The following node pool will be deleted.', [
                  '[{name}] in cluster [{cluster}] in [{region}]'.format(
                      name=node_pool_ref.awsNodePoolsId,
                      cluster=node_pool_ref.awsClustersId,
                      region=node_pool_ref.locationsId)
              ]),
          throw_if_unattended=True,
          cancel_on_no=True)

    with endpoint_util.GkemulticloudEndpointOverride(node_pool_ref.locationsId,
                                                     release_track):
      node_pool_client = node_pools.NodePoolsClient(track=release_track)
      op = node_pool_client.Delete(node_pool_ref, args)
      op_ref = resource_args.GetOperationResource(op)

      if validate_only:
        args.format = 'disable'
        return

      async_ = getattr(args, 'async_', False)
      if not async_:
        waiter.WaitFor(
            waiter.CloudOperationPollerNoResources(
                node_pool_client.client.projects_locations_operations),
            op_ref,
            'Deleting node pool {}'.format(node_pool_ref.awsNodePoolsId),
            wait_ceiling_ms=constants.MAX_LRO_POLL_INTERVAL_MS)

      log.DeletedResource(node_pool_ref)
