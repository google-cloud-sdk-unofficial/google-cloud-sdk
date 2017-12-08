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

"""bigtable clusters update command."""

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateClusterAlpha(base.Command):
  """Update a Bigtable cluster's friendly name and serving nodes."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    util.AddClusterIdArgs(parser)
    util.AddClusterInfoArgs(parser)

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
    msg = self.context['clusteradmin-msgs'].Cluster(
        name=util.ClusterUrl(args),
        displayName=args.description,
        serveNodes=args.nodes)
    result = cli.projects_zones_clusters.Update(msg)
    if not args.async:
      util.WaitForOp(
          self.context,
          result.currentOperation.name,
          'Updating cluster')
    return result

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    # Always use this log module for printing (never use print directly).
    # This allows us to control the verbosity of commands in a global way.
    writer = log.out
    writer.Print('Cluster [{0}] in zone [{1}] update{2}.'.format(
        args.cluster, args.zone, ' in progress' if args.async else 'd'))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateCluster(base.Command):
  """Update a Bigtable cluster's friendly name and serving nodes."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    (arguments.ArgAdder(parser).AddCluster().AddInstance(positional=False)
     .AddClusterNodes().AddAsync())

  @util.MapHttpError
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    cli = util.GetAdminClient()
    msgs = util.GetAdminMessages()
    ref = resources.Parse(
        args.cluster,
        params={'instancesId': args.instance},
        collection='bigtableadmin.projects.instances.clusters')
    msg = msgs.BigtableadminProjectsInstancesClustersUpdateRequest(
        projectsId=ref.projectsId,
        instancesId=ref.instancesId,
        clustersId=ref.Name(),
        cluster=msgs.Cluster(name=ref.Name(),
                             serveNodes=args.num_nodes))
    result = cli.projects_instances_clusters.Update(msg)
    if not args.async:
      # TODO(user): enable this line when b/29563942 is fixed in apitools
      pass
      # util.WaitForOpV2(result, 'Updating cluster')
    return result
