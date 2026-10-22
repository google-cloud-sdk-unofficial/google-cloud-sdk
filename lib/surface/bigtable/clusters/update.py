# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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


import textwrap

from googlecloudsdk.api_lib.bigtable import clusters
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class UpdateCluster(base.UpdateCommand):
  """Update a Bigtable cluster's number of nodes."""

  _support_node_scaling_factor = False

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To update a cluster to `10` nodes, run:

            $ {command} my-cluster-id --instance=my-instance-id --num-nodes=10

          """),
  }

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    arguments.AddClusterResourceArg(parser, 'to update')
    (
        arguments.ArgAdder(parser)
        .AddAsync()
        .AddScalingArgsForClusterUpdate(
            add_node_scaling_factor=cls._support_node_scaling_factor
        )
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      None
    """
    return self._Run(args)

  def _Run(self, args):
    """Implements Run() with different possible features flags."""
    cluster_ref = args.CONCEPTS.cluster.Parse()
    if self._support_node_scaling_factor and args.IsSpecified(
        'node_scaling_factor'
    ):
      request_msg = util.GetAdminMessages().UpdateNodeScalingFactorRequest
      nsf_enum = request_msg.NodeScalingFactorValueValuesEnum
      operation = clusters.UpdateNodeScalingFactor(
          cluster_ref,
          arg_utils.ChoiceToEnum(
              args.node_scaling_factor,
              nsf_enum,
              valid_choices=arguments.GetValidNodeScalingFactors(),
          ),
      )
    else:
      operation = clusters.PartialUpdate(
          cluster_ref,
          nodes=args.num_nodes,
          autoscaling_min=args.autoscaling_min_nodes,
          autoscaling_max=args.autoscaling_max_nodes,
          autoscaling_cpu_target=args.autoscaling_cpu_target,
          autoscaling_storage_target=args.autoscaling_storage_target,
          disable_autoscaling=args.disable_autoscaling,
      )
    if not args.async_:
      operation_ref = util.GetOperationRef(operation)
      return util.AwaitCluster(
          operation_ref,
          'Updating bigtable cluster {0}'.format(cluster_ref.Name()))

    log.UpdatedResource(
        cluster_ref.Name(), kind='cluster', is_async=args.async_)
    return None


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateClusterAlpha(UpdateCluster):
  """Update a Cloud Bigtable cluster's node count or scaling settings."""

  # TODO: b/568765572 - Unhide --node-scaling-factor and promote to BETA (then
  # GA) once the TRUSTED_TESTER_2X_MIGRATION visibility label is removed.
  _support_node_scaling_factor = True
