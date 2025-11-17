# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Bigtable memory layer update command."""

import textwrap

from googlecloudsdk.api_lib.bigtable import memory_layers
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import log


def _UpdateMemoryLayer(cluster_ref, args):
  """Updates a cluster memory layer with the given arguments.

  Args:
    cluster_ref: A resource reference of the cluster to update.
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Returns:
    Long running operation.
  """
  if args.disable:
    return memory_layers.Disable(cluster_ref)
  else:  # args.fixed_capacity must be true due to mutually exclusive group
    storage_size_gib = args.fixed_capacity.get('storage-size-gib')
    max_request_units_per_second = args.fixed_capacity.get(
        'max-request-units-per-second'
    )

    return memory_layers.Update(
        cluster_ref,
        storage_size_gib=storage_size_gib,
        max_request_units_per_second=max_request_units_per_second,
    )


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateMemoryLayer(base.UpdateCommand):
  """Update a Bigtable memory layer."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
          To enable or resize a memory layer, run:

            $ {command} my-cluster-id --instance=my-instance-id --fixed-capacity=storage-size-gib=16,max-request-units-per-second=200000

          To disable a memory layer, run:

            $ {command} my-cluster-id --instance=my-instance-id --disable

          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddClusterResourceArg(parser, 'of the memory layer to update')
    # We need one of these two mutually exclusive groups:
    #   --disable
    #   --fixed-capacity
    update_group = parser.add_mutually_exclusive_group(required=True)
    arguments.ArgAdder(update_group).AddMemoryLayerFixedCapacity()
    arguments.ArgAdder(update_group).AddMemoryLayerDisable()
    arguments.ArgAdder(parser).AddAsync()

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Updated resource.
    """
    del self  # Unused.
    cluster_ref = args.CONCEPTS.cluster.Parse()
    operation = _UpdateMemoryLayer(cluster_ref, args)
    if not args.async_:
      operation_ref = util.GetOperationRef(operation)
      return util.AwaitMemoryLayer(
          operation_ref,
          f'Updating memory layer for cluster [{cluster_ref.Name()}]',
      )

    log.UpdatedResource(
        cluster_ref.RelativeName() + '/memoryLayer',
        kind='memory layer',
        is_async=args.async_,
    )
    return None
