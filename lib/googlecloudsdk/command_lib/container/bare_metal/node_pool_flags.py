# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Helpers for flags in commands for Anthos clusters on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.container.bare_metal import cluster_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def NodePoolAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='node_pool', help_text='node pool of the {resource}.')


def GetNodePoolResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.bareMetalClusters.bareMetalNodePools',
      resource_name='node_pool',
      bareMetalNodePoolsId=NodePoolAttributeConfig(),
      bareMetalClustersId=cluster_flags.ClusterAttributeConfig(),
      locationsId=cluster_flags.LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddNodePoolResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Bare Metal node pool.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'node_pool' if positional else '--node-pool'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetNodePoolResourceSpec(),
      'node pool {}'.format(verb),
      required=True).AddToParser(parser)


def AddAllowMissingNodePool(parser):
  """Adds a flag for the node pool operation to return success and perform no action when there is no matching node pool.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help='If set, and the Bare Metal Node Pool is not found, the request will succeed but no action will be taken.',
  )


# TODO(b/257292798): Move to a shared location.
def AddAllowMissingUpdateNodePool(parser):
  """Adds a flag to enable allow missing in an update node pool request.

  If set to true, and the Bare Metal Node Pool is not found, the request will
  create a new Bare Metal Node Pool with the provided configuration. The user
  must have both create and update permission to call Update with allow_missing
  set to true.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help='If set, and the Anthos cluster on bare metal is not found, the update request will try to create a new cluster with the provided configuration.',
  )


def AddNodePoolDisplayName(parser):
  """Adds a flag to specify the display name of the node pool.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--display-name', type=str, help='Display name for the resource.')


def AddNodePoolAnnotations(parser):
  """Adds a flag to specify node pool annotations."""
  parser.add_argument(
      '--annotations',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='Annotations on the node pool.',
  )


def AddNodePoolConfig(parser, is_update=False):
  """Adds a command group to set the node pool config.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_node_pool_config_group = parser.add_group(
      required=required,
      help='Anthos on bare metal node pool configuration.',
  )
  _AddNodeConfigs(bare_metal_node_pool_config_group, is_update)
  _AddNodeLabels(bare_metal_node_pool_config_group)
  _AddNodeTaints(bare_metal_node_pool_config_group)


def _AddNodeConfigs(bare_metal_node_pool_config_group, is_update=False):
  """Adds flags to set the node configs.

  Args:
    bare_metal_node_pool_config_group: The parent group to add the
      flags to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  node_pool_configs_from_file_help_text = """
Path of the YAML/JSON file that contains the node configs.

Examples:

  nodeConfigs:
  - nodeIp: 10.200.0.10
    labels:
      node1: label1
      node2: label2
  - nodeIp: 10.200.0.11
    labels:
      node3: label3
      node4: label4

List of supported fields in `nodeConfigs`

KEY           | VALUE                     | NOTE
--------------|---------------------------|---------------------------
nodeIp        | string                    | required, mutable
labels        | one or more key-val pairs | optional, mutable

"""
  bare_metal_node_pool_config_group.add_argument(
      '--node-configs-from-file',
      required=required,
      help=node_pool_configs_from_file_help_text,
      type=arg_parsers.YAMLFileContents(),
  )


def _AddNodeLabels(bare_metal_node_pool_config_group):
  """Adds a flag to assign labels to nodes in a node pool.

  Args:
    bare_metal_node_pool_config_group: The parent group to add the flags to.
  """
  bare_metal_node_pool_config_group.add_argument(
      '--node-labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='Labels assigned to nodes of a node pool.',
  )


def _AddNodeTaints(bare_metal_node_pool_config_group):
  """Adds a flag to specify the node taint in the node pool.

  Args:
    bare_metal_node_pool_config_group: The parent group to add the flags to.
  """
  bare_metal_node_pool_config_group.add_argument(
      '--node-taints',
      metavar='KEY=VALUE:EFFECT',
      help='Node taint applied to every Kubernetes node in a node pool.',
      type=arg_parsers.ArgDict(),
  )
