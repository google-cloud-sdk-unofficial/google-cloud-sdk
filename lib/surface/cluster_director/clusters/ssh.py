# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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

"""Command to SSH into instances of a Cluster Director cluster."""

import textwrap
from typing import Any, Optional

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.hypercomputecluster import utils as api_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.cluster_director.clusters import errors
from googlecloudsdk.command_lib.cluster_director.clusters import utils
from googlecloudsdk.command_lib.compute import ssh_utils as compute_ssh_utils
from googlecloudsdk.command_lib.compute.instance_groups import (
    ssh_utils as ig_ssh_utils,
)
from googlecloudsdk.core import resources


DETAILED_HELP = {
    'brief': 'SSH into instances of a Cluster Director cluster.',
    'DESCRIPTION': textwrap.dedent("""
        *{command}* runs an SSH command concurrently on all active VM instances
        in specified Managed Instance Groups of a Managed Compute Cluster
        (unless `--batch-size` is specified).

        Within a batch, all instances are executed concurrently even if the
        command fails on some instances. When executing across multiple batches
        (via `--batch-size`), if the command fails on any instance in a batch,
        subsequent batches are not executed. After execution completes, a
        summary of succeeded, failed (with their exit codes), and skipped
        instances is printed to standard error. If the command succeeds on
        all target instances, *{command}* exits with status `0`. If the
        command fails on one or more instances, *{command}* exits with the first
        non-zero exit status encountered (`255` for SSH connection or client
        errors, or the remote command's non-zero exit code).
        """),
    'EXAMPLES': textwrap.dedent("""
        To run an SSH command concurrently on all active instances in Managed
        Instance Group `mig1` of cluster `my-cluster` in location
        `us-central1-a`, run:

          $ {command} my-cluster --location=us-central1-a \\
              --managed-instance-groups=mig1 --command="hostname"

        To run an SSH command on all active instances across multiple Managed
        Instance Groups `mig1` and `mig2` in batches of 4 concurrent
        connections, run:

          $ {command} my-cluster --location=us-central1-a \\
              --managed-instance-groups=mig1,mig2 --command="uptime" \\
              --batch-size=4
        """),
}


@base.RegionalEndpointsSupported
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Ssh(base.Command):
  """SSH into instances of a Cluster Director cluster."""

  @classmethod
  def Args(cls, parser):
    """Specifies command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    api_version = api_utils.GetApiVersion(cls.ReleaseTrack())
    utils.AddClusterNameArgToParser(parser=parser, api_version=api_version)
    parser.add_argument(
        '--managed-instance-groups',
        required=True,
        type=arg_parsers.ArgList(element_type=str),
        metavar='MANAGED_INSTANCE_GROUP',
        help=(
            'Comma-separated list of Compute Engine Managed Instance Group IDs '
            'or resource names to run the SSH command on.'
        ),
    )
    compute_ssh_utils.BaseSSHCLIHelper.Args(parser)
    ig_ssh_utils.AddSshFlags(parser)

  def _NodeMatchesTarget(self, node: Any, args: Any) -> bool:
    """Returns True if the node matches the target MIGs flag."""
    ce_details = node.computeEngineDetails
    if ce_details is None or not ce_details.instanceGroupManager:
      return False
    igm = ce_details.instanceGroupManager
    return any(
        igm == mig or igm.endswith(f'/instanceGroupManagers/{mig}')
        for mig in args.managed_instance_groups
    )

  def _IsNodeActive(self, node: Any, messages: Any) -> bool:
    """Returns True if the node is ACTIVE or running."""
    ce_details = node.computeEngineDetails
    return (
        node.state == messages.Node.StateValueValuesEnum.ACTIVE
        or (
            node.state is None
            and ce_details is not None
            and ce_details.state == 'RUNNING'
        )
    )

  def _GetInstanceRef(
      self, node: Any, cluster_ref: Any
  ) -> Optional[resources.Resource]:
    """Parses or creates a compute.instances resource reference for node."""
    ce_details = node.computeEngineDetails
    if ce_details is not None and ce_details.instance:
      return resources.REGISTRY.Parse(
          ce_details.instance,
          collection='compute.instances',
      )
    if node.name and node.zone:
      instance_name = node.name.split('/')[-1]
      return resources.REGISTRY.Create(
          'compute.instances',
          project=cluster_ref.projectsId,
          zone=node.zone,
          instance=instance_name,
      )
    return None

  def Run(self, args):
    """Executes the SSH command on all active instances matching target."""
    cluster_ref = args.CONCEPTS.cluster.Parse()
    release_track = self.ReleaseTrack()
    client = api_utils.GetClientInstance(release_track)
    messages = api_utils.GetMessagesModule(release_track)

    cluster = api_utils.GetCluster(client, args, messages)
    if (
        cluster.orchestrator is None
        or cluster.orchestrator.computeEngine is None
    ):
      raise errors.ClusterDirectorError(
          f'Cluster [{cluster_ref.Name()}] does not use a Compute Engine '
          'orchestrator. This command is only supported on Managed Compute '
          'Clusters.'
      )

    list_req = (
        messages.HypercomputeclusterProjectsLocationsClustersNodesListRequest(
            parent=cluster_ref.RelativeName(),
        )
    )
    nodes = list_pager.YieldFromList(
        client.projects_locations_clusters_nodes,
        list_req,
        field='nodes',
        batch_size_attribute='pageSize',
    )

    instance_refs = []
    for node in nodes:
      if self._NodeMatchesTarget(node, args) and self._IsNodeActive(
          node, messages
      ):
        instance_ref = self._GetInstanceRef(node, cluster_ref)
        if instance_ref:
          instance_refs.append(instance_ref)

    if not instance_refs:
      target_vals = ', '.join(args.managed_instance_groups)
      raise exceptions.BadArgumentException(
          '--managed-instance-groups',
          f'No running instances found in instance group [{target_vals}].',
      )

    return ig_ssh_utils.RunSshOnInstances(self, args, instance_refs)


Ssh.detailed_help = DETAILED_HELP
