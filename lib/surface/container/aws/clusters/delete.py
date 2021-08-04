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
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import clusters
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.container.gkemulticloud import operations
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete a GKE cluster on AWS."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    resource_args.AddAwsClusterResourceArg(parser, 'to delete')

    flags.AddValidateOnly(parser, 'cluster to delete')

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the delete command."""
    release_track = self.ReleaseTrack()

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAwsClusterResourceArg(args).locationsId,
        release_track):
      # Parsing again after endpoint override is set.
      cluster_ref = resource_args.ParseAwsClusterResourceArg(args)
      cluster_client = clusters.Client(track=release_track)

      validate_only = getattr(args, 'validate_only', False)
      if not validate_only:
        cluster = cluster_client.Get(cluster_ref)
        console_io.PromptContinue(
            message=gke_util.ConstructList(
                'The following clusters will be deleted.', [
                    '[{name}] in AWS region [{region}]'.format(
                        name=cluster_ref.awsClustersId,
                        region=cluster.awsRegion)
                ]),
            throw_if_unattended=True,
            cancel_on_no=True)

      op = cluster_client.Delete(cluster_ref, args)
      op_ref = resource_args.GetOperationResource(op)

      if validate_only:
        args.format = 'disable'
        return

      log.CreatedResource(op_ref, kind=constants.LRO_KIND)

      async_ = getattr(args, 'async_', False)
      if not async_:
        op_client = operations.Client(track=release_track)
        op_client.Wait(
            op_ref, 'Deleting cluster {} in AWS region {}'.format(
                cluster_ref.awsClustersId, cluster.awsRegion))

      log.DeletedResource(
          cluster_ref, kind=constants.AWS_CLUSTER_KIND, is_async=async_)
