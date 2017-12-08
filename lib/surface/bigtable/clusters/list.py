# Copyright 2016 Google Inc. All Rights Reserved.
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

"""bigtable clusters list command."""


from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_projector


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListClustersAlpha(base.ListCommand):
  """List existing Bigtable clusters."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    pass

  @util.MapHttpError
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    cli = self.context['clusteradmin']
    msg = (self.context['clusteradmin-msgs'].
           BigtableclusteradminProjectsAggregatedClustersListRequest(
               name=util.ProjectUrl()))
    clusters = cli.projects_aggregated_clusters.List(msg).clusters
    return [ClusterDict(cluster) for cluster in clusters]

  def Collection(self):
    return 'bigtable.clusters.list.alpha'


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListClusters(base.ListCommand):
  """List existing Bigtable clusters."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.ArgAdder(parser).AddInstance(positional=False,
                                           required=False,
                                           multiple=True)

  @util.MapHttpError
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      Some value that we want to have printed later.
    """
    cli = util.GetAdminClient()
    instances = args.instances or ['-']
    # can't use list_pager due to b/29450218
    for instance in instances:
      ref = resources.Parse(instance,
                            collection='bigtableadmin.projects.instances')
      msg = (util.GetAdminMessages()
             .BigtableadminProjectsInstancesClustersListRequest(
                 projectsId=ref.projectsId,
                 instancesId=ref.Name()))
      clusters = cli.projects_instances_clusters.List(msg).clusters
      for cluster in clusters:
        yield cluster

  def Collection(self):
    return 'bigtable.clusters.list'


def ClusterDict(cluster):
  """Returns a cluster dict zone_id and cluster_id fields added."""
  result = resource_projector.MakeSerializable(cluster)
  zone_id, cluster_id = util.ExtractZoneAndCluster(cluster.name)
  result['zoneId'] = zone_id
  result['clusterId'] = cluster_id
  return result
