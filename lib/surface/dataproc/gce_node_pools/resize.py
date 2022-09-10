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
"""Resize a GCE node pool command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
import six


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Resize(base.Command):
  """Resize the number of nodes in the Compute Engine node pool."""
  detailed_help = {
      'EXAMPLES':
          """\
          To resize a node pool, run:

            $ {command} my-gce-node-pool-id --region=us-central1 --cluster=my-cluster-name --size=5
          """
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())

    flags.AddGceNodePoolResourceArg(parser, 'resize', dataproc.api_version)
    flags.AddSizeFlag(parser)
    flags.AddGracefulDecommissionTimeoutFlag(parser)
    flags.AddTimeoutFlag(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    messages = dataproc.messages

    gce_node_pool = args.CONCEPTS.gce_node_pool.Parse()

    resize_request = messages.ResizeGceNodePoolRequest(
        size=args.size, requestId=util.GetUniqueId())
    if args.graceful_decommission_timeout is not None:
      resize_request.gracefulDecommissionTimeout = (
          six.text_type(args.graceful_decommission_timeout) + 's')

    request = messages.DataprocProjectsRegionsClustersGceNodePoolsResizeRequest(
        name=gce_node_pool.RelativeName(),
        resizeGceNodePoolRequest=resize_request)

    operation = dataproc.client.projects_regions_clusters_gceNodePools.Resize(
        request)

    util.WaitForOperation(
        dataproc,
        operation,
        message='Waiting for node pool resize operation',
        timeout_s=args.timeout)

    request = messages.DataprocProjectsRegionsClustersGceNodePoolsGetRequest(
        name=gce_node_pool.RelativeName())
    final_gce_node_pool = dataproc.client.projects_regions_clusters_gceNodePools.Get(
        request)
    log.UpdatedResource(gce_node_pool)

    return final_gce_node_pool
