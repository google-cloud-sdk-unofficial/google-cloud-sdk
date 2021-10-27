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
"""Command to update an Anthos cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import clusters
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.container.gkemulticloud import operations
from googlecloudsdk.core import log

# Command needs to be in one line for the docgen tool to format properly.
_EXAMPLES = """
To update a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1 --cluster-version=CLUSTER_VERSION
"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update an Anthos cluster on AWS."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAwsClusterResourceArg(parser, 'to update')
    flags.AddClusterVersion(parser, required=False)
    flags.AddValidateOnly(parser, 'update of the cluster')
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat(clusters.CLUSTERS_FORMAT)

  def Run(self, args):
    """Runs the update command."""
    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAwsClusterResourceArg(args).locationsId,
        self.ReleaseTrack()):

      cluster_ref = resource_args.ParseAwsClusterResourceArg(args)
      cluster_client = clusters.Client(track=self.ReleaseTrack())
      op = cluster_client.Update(cluster_ref, args)
      op_ref = resource_args.GetOperationResource(op)

      validate_only = getattr(args, 'validate_only', False)
      if validate_only:
        args.format = 'disable'
        return

      log.CreatedResource(op_ref, kind=constants.LRO_KIND)

      async_ = getattr(args, 'async_', False)
      if not async_:
        op_client = operations.Client(track=self.ReleaseTrack())
        op_client.Wait(op_ref,
                       'Updating cluster {}.'.format(cluster_ref.awsClustersId))

      log.UpdatedResource(
          cluster_ref, kind=constants.AWS_CLUSTER_KIND, is_async=async_)
      return cluster_client.Get(cluster_ref)
