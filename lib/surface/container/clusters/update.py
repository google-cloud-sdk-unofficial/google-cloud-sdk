# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Update cluster command."""
import argparse

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.third_party.apitools.base.py import exceptions as apitools_exceptions


class InvalidAddonValueError(util.Error):
  """A class for invalid --update-addons input."""

  def __init__(self, value):
    message = ('invalid --update-addons value {0}; '
               'must be ENABLED or DISABLED.'.format(value))
    super(InvalidAddonValueError, self).__init__(message)


def _ParseAddonDisabled(val):
  if val == 'ENABLED':
    return False
  if val == 'DISABLED':
    return True
  raise InvalidAddonValueError(val)


class Update(base.Command):
  """Update cluster settings for an existing container cluster."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        'name',
        metavar='NAME',
        help='The name of the cluster to update.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--monitoring-service',
        help='The monitoring service to use for the cluster. Options '
        'are: "monitoring.googleapis.com" (the Google Cloud Monitoring '
        'service),  "none" (no metrics will be exported from the cluster)')
    group.add_argument(
        '--update-addons',
        type=arg_parsers.ArgDict(spec={
            api_adapter.INGRESS: _ParseAddonDisabled,
            api_adapter.HPA: _ParseAddonDisabled,
        }),
        dest='disable_addons',
        action=arg_parsers.FloatingListValuesCatcher(),
        metavar='ADDON=ENABLED|DISABLED',
        help='''Cluster addons to enable or disable. Options are
  {hpa}=ENABLED|DISABLED
  {ingress}=ENABLED|DISABLED'''.format(
      hpa=api_adapter.HPA, ingress=api_adapter.INGRESS))
    parser.add_argument(
        '--node-pool',
        help=argparse.SUPPRESS)
    flags.AddClusterAutoscalingFlags(parser, group)
    flags.AddClustersWaitAndAsyncFlags(parser)

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
    # Make sure it exists (will raise appropriate error if not)
    adapter.GetCluster(cluster_ref)

    options = api_adapter.UpdateClusterOptions(
        monitoring_service=args.monitoring_service,
        disable_addons=args.disable_addons,
        enable_autoscaling=args.enable_autoscaling,
        min_nodes=args.min_nodes,
        max_nodes=args.max_nodes,
        node_pool=args.node_pool)

    try:
      op_ref = adapter.UpdateCluster(cluster_ref, options)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(util.GetError(error))

    if not flags.GetAsyncValueFromAsyncAndWaitFlags(args.async, args.wait):
      adapter.WaitForOperation(
          op_ref, 'Updating {0}'.format(cluster_ref.clusterId))

      log.UpdatedResource(cluster_ref)
