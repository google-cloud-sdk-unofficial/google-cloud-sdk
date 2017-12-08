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

from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.third_party.apitools.base.py import exceptions as apitools_exceptions


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
  # Timeout in seconds for operation
  parser.add_argument(
      '--timeout',
      type=int,
      default=1800,
      help=argparse.SUPPRESS)
  parser.add_argument(
      '--wait',
      action='store_true',
      default=True,
      help='Poll the operation for completion after issuing a create request.')
  parser.add_argument(
      '--num-nodes',
      type=int,
      help='The number of nodes in the node pool.',
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


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Create a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def ParseCreateNodePoolOptions(self, args):
    return api_adapter.CreateNodePoolOptions(
        machine_type=args.machine_type,
        disk_size_gb=args.disk_size,
        scopes=args.scopes,
        num_nodes=args.num_nodes)

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
    options = self.ParseCreateNodePoolOptions(args)

    try:
      if not args.scopes:
        args.scopes = []
      pool_ref = adapter.ParseNodePool(args.name)
      options = self.ParseCreateNodePoolOptions(args)
      operation_ref = adapter.CreateNodePool(pool_ref, options)
      if not args.wait:
        return adapter.GetNodePool(pool_ref)

      adapter.WaitForOperation(
          operation_ref,
          'Creating node pool {0}'.format(pool_ref.nodePoolId),
          timeout_s=args.timeout)
      pool = adapter.GetNodePool(pool_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(util.GetError(error))

    log.CreatedResource(pool_ref)
    return pool

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    self.context['api_adapter'].PrintNodePools([result])
