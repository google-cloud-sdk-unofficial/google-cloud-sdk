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
"""Command to get kubeconfig of a GKE cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import clusters
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetKubeconfig(base.Command):
  """Get kubeconfig of a GKE cluster on AWS."""

  @staticmethod
  def Args(parser):
    resource_args.AddAwsClusterResourceArg(parser, 'to get kubeconfig')
    flags.AddOutputFile(parser, 'to store kubeconfig')

  def Run(self, args):
    """Run the get-kubeconfig command."""
    release_track = self.ReleaseTrack()

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAwsClusterResourceArg(args).locationsId,
        release_track):
      # Parsing again after endpoint override is set.
      cluster_ref = resource_args.ParseAwsClusterResourceArg(args)
      cluster_client = clusters.Client(track=release_track)
      resp = cluster_client.GetKubeconfig(cluster_ref)
      log.WriteToFileOrStdout(
          args.output_file if args.output_file else '-',
          resp.kubeconfig,
          overwrite=True,
          binary=False,
          private=True)
