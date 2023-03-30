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
"""Command to get credentials of a GEC cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import util as container_util
from googlecloudsdk.api_lib.edge_cloud.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.container import flags
from googlecloudsdk.command_lib.edge_cloud.container import kubeconfig
from googlecloudsdk.command_lib.edge_cloud.container import resource_args
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class GetCredentials(base.Command):
  """Get credentials of an edge-container cluster."""

  detailed_help = {
      'EXAMPLES':
          kubeconfig.COMMAND_EXAMPLE,
      'DESCRIPTION':
          kubeconfig.COMMAND_DESCRIPTION.format(kind='Edge Container')
  }

  @staticmethod
  def Args(parser):
    resource_args.AddClusterResourceArg(parser, 'to get credentials')
    flags.AddAuthProviderCmdPath(parser)

  def Run(self, args):
    """Runs the get-credentials command."""
    container_util.CheckKubectlInstalled()

    cluster_ref = resources.REGISTRY.ParseRelativeName(
        args.CONCEPTS.cluster.Parse().RelativeName(),
        collection='edgecontainer.projects.locations.clusters')

    messages = util.GetMessagesModule(self.ReleaseTrack())
    cluster_client = util.GetClientInstance(self.ReleaseTrack())
    req = messages.EdgecontainerProjectsLocationsClustersGetRequest(
        name=cluster_ref.RelativeName())
    resp = cluster_client.projects_locations_clusters.Get(req)
    context = kubeconfig.GenerateContext(cluster_ref.projectsId,
                                         cluster_ref.locationsId,
                                         cluster_ref.clustersId)
    cmd_args = kubeconfig.GenerateAuthProviderCmdArgs(
        self.ReleaseTrack(), cluster_ref.clustersId,
        cluster_ref.projectsId, cluster_ref.locationsId)

    exec_auth_args = kubeconfig.GenerateExecAuthCmdArgs(
        cluster_ref.clustersId,
        cluster_ref.projectsId,
        cluster_ref.locationsId,
    )

    kubeconfig.GenerateKubeconfig(resp, context, args.auth_provider_cmd_path,
                                  cmd_args, exec_auth_args)
