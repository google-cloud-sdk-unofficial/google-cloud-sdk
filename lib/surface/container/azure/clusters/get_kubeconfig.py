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
"""Get the kubeconfig for an Azure cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.azure import util as azure_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetKubeconfig(base.DescribeCommand):
  """Get the kubeconfig for an Azure cluster."""

  @staticmethod
  def Args(parser):
    resource_args.AddAzureClusterResourceArg(parser, 'to get the kubeconfig')
    flags.AddOutputFile(parser, 'to store kubeconfig')

  def Run(self, args):
    """Run the get-kubeconfig command."""

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureClusterResourceArg(args).locationsId,
        self.ReleaseTrack()):
      # Parsing again after endpoint override is set.
      cluster_ref = resource_args.ParseAzureClusterResourceArg(args)
      api_client = azure_api_util.ClustersClient(track=self.ReleaseTrack())
      resp = api_client.GetKubeConfig(cluster_ref)
      log.WriteToFileOrStdout(
          args.output_file if args.output_file else '-',
          resp.kubeconfig,
          overwrite=True,
          binary=False,
          private=True)
