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

"""Create node pool command."""

import argparse

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


DETAILED_HELP = {
    'DESCRIPTION': """\
        *{command}* facilitates the creation of a node pool in a Google
        Container Engine cluster. A variety of options exists to customize the
        node configuration and the number of nodes created.
        """,
    'EXAMPLES': """\
        To create a new node pool "node-pool-1" with the default options in the
        cluster "sample-cluster", run:

          $ {command} node-pool-1 --cluster=sample-cluster

        The new node pool will show up in the cluster after all the nodes have
        been provisioned.

        To create a node pool with 5 nodes, run:

          $ {command} node-pool-1 --cluster=sample-cluster --num-nodes=5
        """,
}


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
  """
  parser.add_argument('name', help='The name of the node pool to create.')
  parser.add_argument(
      '--cluster',
      help='The cluster to add the node pool to.',
      action=actions.StoreProperty(properties.VALUES.container.cluster))
  parser.add_argument(
      '--enable-cloud-endpoints',
      action='store_true',
      default=True,
      help='Automatically enable Google Cloud Endpoints to take advantage of '
      'API management features.')
  # Timeout in seconds for operation
  parser.add_argument(
      '--timeout',
      type=int,
      default=1800,
      help=argparse.SUPPRESS)
  parser.add_argument(
      '--num-nodes',
      type=int,
      help='The number of nodes in the node pool in each of the '
      'cluster\'s zones.',
      default=3)
  parser.add_argument(
      '--machine-type', '-m',
      help='The type of machine to use for nodes. Defaults to '
      'server-specified')
  parser.add_argument(
      '--disk-size',
      type=int,
      help='Size in GB for node VM boot disks. Defaults to 100GB.')
  parser.add_argument(
      '--scopes',
      type=arg_parsers.ArgList(min_length=1),
      metavar='SCOPE',
      action=arg_parsers.FloatingListValuesCatcher(),
      help="""\
Specifies scopes for the node instances. The project's default
service account is used. Examples:

  $ {{command}} example-cluster --scopes https://www.googleapis.com/auth/devstorage.read_only

  $ {{command}} example-cluster --scopes bigquery,storage-rw,compute-ro

Multiple SCOPEs can specified, separated by commas. The scopes
necessary for the cluster to function properly (compute-rw, storage-ro),
are always added, even if not explicitly specified.

SCOPE can be either the full URI of the scope or an alias.
Available aliases are:

Alias,URI
{aliases}
""".format(
    aliases='\n        '.join(
        ','.join(value) for value in
        sorted(constants.SCOPES.iteritems()))))
  parser.add_argument(
      '--tags',
      help=argparse.SUPPRESS,
      type=arg_parsers.ArgList(min_length=1),
      metavar='TAGS',
      action=arg_parsers.FloatingListValuesCatcher())


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddImageTypeFlag(parser, 'node pool', suppressed=False)
    flags.AddClusterAutoscalingFlags(parser, suppressed=True)
    flags.AddLocalSSDFlag(parser, suppressed=True)

  def ParseCreateNodePoolOptions(self, args):
    return api_adapter.CreateNodePoolOptions(
        machine_type=args.machine_type,
        disk_size_gb=args.disk_size,
        scopes=args.scopes,
        enable_cloud_endpoints=args.enable_cloud_endpoints,
        num_nodes=args.num_nodes,
        local_ssd_count=args.local_ssd_count,
        tags=args.tags,
        enable_autoscaling=args.enable_autoscaling,
        max_nodes=args.max_nodes,
        min_nodes=args.min_nodes,
        image_type=args.image_type)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Cluster message for the successfully created node pool.

    Raises:
      util.Error, if creation failed.
    """
    adapter = self.context['api_adapter']

    if not args.scopes:
      args.scopes = []

    try:
      if not args.scopes:
        args.scopes = []
      pool_ref = adapter.ParseNodePool(args.name)
      options = self.ParseCreateNodePoolOptions(args)
      operation_ref = adapter.CreateNodePool(pool_ref, options)

      adapter.WaitForOperation(
          operation_ref,
          'Creating node pool {0}'.format(pool_ref.nodePoolId),
          timeout_s=args.timeout)
      pool = adapter.GetNodePool(pool_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(util.GetError(error))

    log.CreatedResource(pool_ref)
    return pool

  def Collection(self):
    return 'container.projects.zones.clusters.nodePools'

  def Format(self, args):
    return self.ListFormat(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddImageTypeFlag(parser, 'node pool')
    flags.AddClusterAutoscalingFlags(parser, suppressed=True)
    flags.AddLocalSSDFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddImageTypeFlag(parser, 'node pool')
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddLocalSSDFlag(parser)


Create.detailed_help = DETAILED_HELP
