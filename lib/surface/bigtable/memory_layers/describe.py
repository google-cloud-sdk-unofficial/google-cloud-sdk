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
"""Bigtable memory layer describe command."""

import textwrap

from googlecloudsdk.api_lib.bigtable import memory_layers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeMemoryLayer(base.DescribeCommand):
  """Describe a Bigtable memory layer."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
          To view a memory layer's description, run:

            $ {command} my-cluster-id --instance=my-instance-id

          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddClusterResourceArg(parser, 'of the memory layer to describe')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    del self  # Unused.
    cluster_ref = args.CONCEPTS.cluster.Parse()
    return memory_layers.Describe(cluster_ref)
