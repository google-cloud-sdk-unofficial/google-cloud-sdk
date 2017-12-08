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

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListClusters(base.ListCommand):
  """List existing Bigtable clusters."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.ArgAdder(parser).AddInstance(
        positional=False, required=False, multiple=True)

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
    for instance in instances:
      ref = resources.REGISTRY.Parse(
          instance, collection='bigtableadmin.projects.instances')
      msg = (util.GetAdminMessages()
             .BigtableadminProjectsInstancesClustersListRequest(
                 parent=ref.RelativeName()))
      for cluster in list_pager.YieldFromList(
          cli.projects_instances_clusters,
          msg,
          field='clusters',
          batch_size_attribute=None):
        yield cluster

  def Collection(self):
    return 'bigtable.clusters.list'
