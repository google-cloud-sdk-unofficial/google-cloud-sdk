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

"""bigtable clusters create command."""

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateCluster(base.Command):
  """Create a new Bigtable cluster."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    util.AddClusterIdArgs(parser)
    util.AddClusterInfoArgs(parser)
    parser.add_argument(
        '--storage',
        choices=['HDD', 'SSD'],
        default='SSD',
        type=str.upper,
        help='Storage class for the cluster. Valid options are HDD or SSD.')

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
    cluster = self.context['clusteradmin-msgs'].Cluster
    storage_options = {
        'HDD': cluster.DefaultStorageTypeValueValuesEnum.STORAGE_HDD,
        'SSD': cluster.DefaultStorageTypeValueValuesEnum.STORAGE_SSD}
    msg = self.context['clusteradmin-msgs'].CreateClusterRequest(
        name=util.ZoneUrl(args),
        clusterId=args.cluster,
        cluster=cluster(
            displayName=args.description,
            serveNodes=args.nodes,
            defaultStorageType=storage_options[args.storage]))
    result = cli.projects_zones_clusters.Create(msg)
    if not args.async:
      util.WaitForOp(
          self.context,
          result.currentOperation.name,
          'Creating cluster')
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
    writer.Print('Cluster [{0}] in zone [{1}] creat{2}.'.format(
        args.cluster, args.zone, 'ion in progress' if args.async else 'ed'))
