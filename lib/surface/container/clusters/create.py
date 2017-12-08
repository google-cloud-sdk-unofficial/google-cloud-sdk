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

"""Create cluster command."""
import argparse
import random
import string

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
  """
  parser.add_argument('name', help='The name of this cluster.')
  # Timeout in seconds for operation
  parser.add_argument(
      '--timeout',
      type=int,
      default=1800,
      help=argparse.SUPPRESS)
  flags.AddClustersWaitAndAsyncFlags(parser)
  parser.add_argument(
      '--num-nodes',
      type=arg_parsers.BoundedInt(1),
      help='The number of nodes to be created in each of the cluster\'s zones.',
      default=3)
  parser.add_argument(
      '--additional-zones',
      type=arg_parsers.ArgList(min_length=1),
      metavar='ZONE',
      action=arg_parsers.FloatingListValuesCatcher(),
      help="""\
The set of additional zones in which the specified node footprint should be
replicated. All zones must be in the same region as the cluster's primary zone.
If additional-zones is not specified, all nodes will be in the cluster's primary
zone.

Note that `NUM_NODES` nodes will be created in each zone, such that if you
specify `--num-nodes=4` and choose one additional zone, 8 nodes will be created.

Multiple locations can be specified, separated by commas. For example:

  $ {{command}} example-cluster --zone us-central1-a --additional-zones us-central1-b,us-central1-c
""")
  parser.add_argument(
      '--machine-type', '-m',
      help='The type of machine to use for nodes. Defaults to '
      'server-specified')
  parser.add_argument(
      '--subnetwork',
      help='The name of the Google Compute Engine subnetwork '
      '(https://cloud.google.com/compute/docs/subnetworks) to which the '
      'cluster is connected. If specified, the cluster\'s network must be a '
      '"custom subnet" network. Specification of subnetworks is an '
      'alpha feature, and requires that the '
      'Google Compute Engine alpha API be enabled.')
  parser.add_argument(
      '--disable-addons',
      type=arg_parsers.ArgList(
          choices=[api_adapter.INGRESS, api_adapter.HPA]),
      help='List of cluster addons to disable. Options are {0}'.format(
          ', '.join([api_adapter.INGRESS, api_adapter.HPA])))
  parser.add_argument(
      '--network',
      help='The Compute Engine Network that the cluster will connect to. '
      'Google Container Engine will use this network when creating routes '
      'and firewalls for the clusters. Defaults to the \'default\' network.')
  parser.add_argument(
      '--cluster-ipv4-cidr',
      help='The IP address range for the pods in this cluster in CIDR '
      'notation (e.g. 10.0.0.0/14). Defaults to server-specified')
  parser.add_argument(
      '--password',
      help='The password to use for cluster auth. Defaults to a '
      'randomly-generated string.')
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

[format="csv",options="header"]
|========
Alias,URI
{aliases}
|========
""".format(
    aliases='\n'.join(
        ','.join(value) for value in
        sorted(constants.SCOPES.iteritems()))))
  parser.add_argument(
      '--enable-cloud-endpoints',
      action='store_true',
      default=True,
      help='Automatically enable Google Cloud Endpoints to take advantage of '
      'API management features.')
  parser.add_argument(
      '--enable-cloud-logging',
      action='store_true',
      default=True,
      help='Automatically send logs from the cluster to the '
      'Google Cloud Logging API.')
  parser.set_defaults(enable_cloud_logging=True)
  parser.add_argument(
      '--enable-cloud-monitoring',
      action='store_true',
      default=True,
      help='Automatically send metrics from pods in the cluster to the '
      'Google Cloud Monitoring API. VM metrics will be collected by Google '
      'Compute Engine regardless of this setting.')
  parser.set_defaults(enable_cloud_monitoring=True)
  parser.add_argument(
      '--disk-size',
      type=int,
      help='Size in GB for node VM boot disks. Defaults to 100GB.')
  parser.add_argument(
      '--username', '-u',
      help='The user name to use for cluster auth.',
      default='admin')
  parser.add_argument(
      '--max-nodes-per-pool',
      type=arg_parsers.BoundedInt(100, api_adapter.MAX_NODES_PER_POOL),
      help='The maximum number of nodes to allocate per default initial node '
      'pool. Container engine will automatically create enough nodes pools '
      'such that each node pool contains less than '
      '--max-nodes-per-pool nodes. Defaults to {nodes} nodes, but can be set '
      'as low as 100 nodes per pool on initial create.'.format(
          nodes=api_adapter.MAX_NODES_PER_POOL))
  parser.add_argument(
      '--cluster-version',
      help=argparse.SUPPRESS)
  parser.add_argument(
      '--tags',
      help=argparse.SUPPRESS,
      type=arg_parsers.ArgList(min_length=1),
      metavar='TAGS',
      action=arg_parsers.FloatingListValuesCatcher())


NO_CERTS_ERROR_FMT = '''\
Failed to get certificate data for cluster; the kubernetes
api may not be accessible. You can retry later by running

{command}'''


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Create a cluster for running containers."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddImageTypeFlag(parser, 'cluster', suppressed=True)
    flags.AddClusterAutoscalingFlags(parser, suppressed=True)
    flags.AddLocalSSDFlag(parser, suppressed=True)

  def ParseCreateOptions(self, args):
    if not args.scopes:
      args.scopes = []
    cluster_ipv4_cidr = args.cluster_ipv4_cidr
    return api_adapter.CreateClusterOptions(
        node_machine_type=args.machine_type,
        scopes=args.scopes,
        enable_cloud_endpoints=args.enable_cloud_endpoints,
        num_nodes=args.num_nodes,
        additional_zones=args.additional_zones,
        user=args.username,
        password=args.password,
        cluster_version=args.cluster_version,
        network=args.network,
        subnetwork=args.subnetwork,
        cluster_ipv4_cidr=cluster_ipv4_cidr,
        node_disk_size_gb=args.disk_size,
        enable_cloud_logging=args.enable_cloud_logging,
        enable_cloud_monitoring=args.enable_cloud_monitoring,
        disable_addons=args.disable_addons,
        local_ssd_count=args.local_ssd_count,
        tags=args.tags,
        enable_autoscaling=args.enable_autoscaling,
        max_nodes=args.max_nodes,
        min_nodes=args.min_nodes,
        image_type=args.image_type,
        max_nodes_per_pool=args.max_nodes_per_pool)

  def Collection(self):
    return 'container.projects.zones.clusters'

  def Format(self, args):
    return self.ListFormat(args)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Cluster message for the successfully created cluster.

    Raises:
      util.Error, if creation failed.
    """
    util.CheckKubectlInstalled()
    if not args.password:
      args.password = ''.join(random.SystemRandom().choice(
          string.ascii_letters + string.digits) for _ in range(16))

    adapter = self.context['api_adapter']

    if not args.scopes:
      args.scopes = []
    cluster_ref = adapter.ParseCluster(args.name)
    options = self.ParseCreateOptions(args)

    operation = None
    try:
      operation_ref = adapter.CreateCluster(cluster_ref, options)
      if flags.GetAsyncValueFromAsyncAndWaitFlags(args.async, args.wait):
        return adapter.GetCluster(cluster_ref)

      operation = adapter.WaitForOperation(
          operation_ref,
          'Creating cluster {0}'.format(cluster_ref.clusterId),
          timeout_s=args.timeout)
      cluster = adapter.GetCluster(cluster_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(util.GetError(error))

    log.CreatedResource(cluster_ref)
    if operation.detail:
      # Non-empty detail on a DONE create operation should be surfaced as
      # a warning to end user.
      log.warning(operation.detail)

    try:
      util.ClusterConfig.Persist(cluster, cluster_ref.projectId)
    except kconfig.MissingEnvVarError as error:
      log.warning(error.message)

    return cluster


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a cluster for running containers."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddImageTypeFlag(parser, 'cluster')
    flags.AddClusterAutoscalingFlags(parser, suppressed=True)
    flags.AddLocalSSDFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a cluster for running containers."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddImageTypeFlag(parser, 'cluster')
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddLocalSSDFlag(parser)
