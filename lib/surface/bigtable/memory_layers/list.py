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
"""bigtable memory layers list command."""

import textwrap

from googlecloudsdk.api_lib.bigtable import memory_layers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import resources


def _GetUriFunction(resource):
  cluster_ref = resources.REGISTRY.ParseRelativeName(
      resource.name.replace('/memoryLayer', ''),
      collection='bigtableadmin.projects.instances.clusters',
  )
  return cluster_ref.SelfLink() + '/memoryLayer'


def _TransformCluster(resource):
  """Get Cluster ID from memory layer name."""
  # memory layer name is in the format of:
  # projects/{}/instances/{}/clusters/{}/memoryLayer
  memory_layer_name = resource.get('name')
  results = memory_layer_name.split('/')
  cluster_name = results[-2]
  return cluster_name


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListMemoryLayers(base.ListCommand):
  """List Bigtable memory layers."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""
          List Bigtable memory layers.
          """),
      'EXAMPLES': textwrap.dedent("""
          To list all memory layers in an instance, run:

            $ {command} --instance=INSTANCE_NAME

          To list all memory layers in a cluster, run:

            $ {command} --instance=INSTANCE_NAME --cluster=CLUSTER_NAME
          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddMemoryLayerListResourceArg(parser, 'to list memory layers for')
    parser.display_info.AddFormat("""
          table(
            cluster():sort=1:label=CLUSTER,
            memoryConfig.storageSizeGib:label=STORAGE_SIZE_GIB,
            state:label=STATE
          )
        """)
    parser.display_info.AddUriFunc(_GetUriFunction)
    parser.display_info.AddTransforms({'cluster': _TransformCluster})

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A generator of memory layer resource objects.
    """
    instance_ref = args.CONCEPTS.instance.Parse()
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_id = args.cluster if args.IsSpecified('cluster') else None

    return memory_layers.List(
        cluster_ref=cluster_ref,
        instance_ref=instance_ref,
        cluster=cluster_id,
    )
