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

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log


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


def _AddCommonArgs(parser):
  parser.add_argument(
      'name',
      metavar='NAME',
      help='The name of the cluster to update.')
  parser.add_argument(
      '--node-pool',
      help='Node pool to be updated.')
  flags.AddClustersWaitAndAsyncFlags(parser)


def _AddMutuallyExclusiveArgs(mutex_group):
  """Add all arguments that need to be mutually eclusive from each other."""
  mutex_group.add_argument(
      '--monitoring-service',
      help='The monitoring service to use for the cluster. Options '
      'are: "monitoring.googleapis.com" (the Google Cloud Monitoring '
      'service),  "none" (no metrics will be exported from the cluster)')
  mutex_group.add_argument(
      '--update-addons',
      type=arg_parsers.ArgDict(spec={
          api_adapter.INGRESS: _ParseAddonDisabled,
          api_adapter.HPA: _ParseAddonDisabled,
      }),
      dest='disable_addons',
      metavar='ADDON=ENABLED|DISABLED',
      help='''Cluster addons to enable or disable. Options are
{hpa}=ENABLED|DISABLED
{ingress}=ENABLED|DISABLED'''.format(
    hpa=api_adapter.HPA, ingress=api_adapter.INGRESS))


def _AddAdditionalZonesArg(mutex_group):
  mutex_group.add_argument(
      '--additional-zones',
      type=arg_parsers.ArgList(),
      metavar='ZONE',
      help="""\
The set of additional zones in which the cluster's node footprint should be
replicated. All zones must be in the same region as the cluster's primary zone.

Note that the exact same footprint will be replicated in all zones, such that
if you created a cluster with 4 nodes in a single zone and then use this option
to spread across 2 more zones, 8 additional nodes will be created.

Multiple locations can be specified, separated by commas. For example:

  $ {{command}} example-cluster --zone us-central1-a --additional-zones us-central1-b,us-central1-c

To remove all zones other than the cluster's primary zone, pass the empty string
to the flag. For example:

  $ {{command}} example-cluster --zone us-central1-a --additional-zones ""
""")


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update cluster settings for an existing container cluster."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    _AddCommonArgs(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    _AddMutuallyExclusiveArgs(group)
    flags.AddClusterAutoscalingFlags(parser, group, hidden=True)

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

    # locations will be None if additional-zones was specified, an empty list
    # if it was specified with no argument, or a populated list if zones were
    # provided. We want to distinguish between the case where it isn't
    # specified (and thus shouldn't be passed on to the API) and the case where
    # it's specified as wanting no additional zones, in which case we must pass
    # the cluster's primary zone to the API.
    # TODO(b/29578401): Remove the hasattr once the flag is GA.
    locations = None
    if hasattr(args, 'additional_zones') and args.additional_zones is not None:
      locations = sorted([cluster_ref.zone] + args.additional_zones)

    options = api_adapter.UpdateClusterOptions(
        monitoring_service=args.monitoring_service,
        disable_addons=args.disable_addons,
        enable_autoscaling=args.enable_autoscaling,
        min_nodes=args.min_nodes,
        max_nodes=args.max_nodes,
        node_pool=args.node_pool,
        locations=locations)

    try:
      op_ref = adapter.UpdateCluster(cluster_ref, options)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    if not flags.GetAsyncValueFromAsyncAndWaitFlags(args.async, args.wait):
      adapter.WaitForOperation(
          op_ref, 'Updating {0}'.format(cluster_ref.clusterId))

      log.UpdatedResource(cluster_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update cluster settings for an existing container cluster."""

  @staticmethod
  def Args(parser):
    _AddCommonArgs(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    _AddMutuallyExclusiveArgs(group)
    flags.AddClusterAutoscalingFlags(parser, group, hidden=True)
    _AddAdditionalZonesArg(group)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update cluster settings for an existing container cluster."""

  @staticmethod
  def Args(parser):
    _AddCommonArgs(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    _AddMutuallyExclusiveArgs(group)
    flags.AddClusterAutoscalingFlags(parser, group)
    _AddAdditionalZonesArg(group)


