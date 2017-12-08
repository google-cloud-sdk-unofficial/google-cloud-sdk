# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Resize cluster command."""
from os import path

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Resize(base.Command):
  """Resizes an existing cluster for running containers."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument('name', help='The name of this cluster.')
    parser.add_argument(
        '--size',
        required=True,
        type=int,
        help=('Target number of nodes in the cluster.'))
    parser.add_argument(
        '--wait',
        action='store_true',
        default=True,
        help='Poll the operation for completion after issuing an resize '
        'request.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    adapter = self.context['api_adapter']
    cluster_ref = adapter.ParseCluster(args.name)
    cluster = adapter.GetCluster(cluster_ref)
    if cluster.currentNodeCount == args.size:
      log.status.Print('Cluster [{cluster_name}] already has a size of '
                       '{current_size}. Please specify a different size.'
                       .format(cluster_name=cluster.name,
                               current_size=cluster.currentNodeCount))
      return

    console_io.PromptContinue(
        message=('Cluster [{cluster_name}] will be resized from '
                 '{current_size} nodes to {new_size} nodes.')
        .format(cluster_name=cluster.name,
                current_size=cluster.currentNodeCount,
                new_size=args.size),
        throw_if_unattended=True,
        cancel_on_no=True)

    # TODO(user): Fix this hack when we support multiple instance groups
    group = path.basename(cluster.instanceGroupUrls[0])

    op_ref = adapter.ResizeCluster(cluster_ref.projectId, cluster.zone, group,
                                   args.size)

    if args.wait:
      op_ref = adapter.WaitForComputeOperation(
          cluster_ref.projectId, cluster.zone, op_ref.name,
          'Resizing {0}'.format(cluster_ref.clusterId))
    return op_ref

Resize.detailed_help = {
    'brief': 'Resizes an existing cluster for running containers.',
    'DESCRIPTION': """
        *{command}* resize an existing cluster to a provided size.

When increasing the size of a container cluster, the new instances are created
with the same configuration as the existing instances.
Existing pods are not moved onto the new instances,
but new pods (such as those created by resizing a replication controller)
will be scheduled onto the new instances.

When decreasing a cluster, the pods that are scheduled on the instances being
removed will be killed. If your pods are being managed by a replication
controller, the controller will attempt to reschedule them onto the remaining
instances. If your pods are not managed by a replication controller,
they will not be restarted.
Note that when resizing down, instances running pods and instances without pods
are not differentiated. Resize will pick instances to remove at random.
""",
}
