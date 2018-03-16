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

"""Create cluster command."""

from googlecloudsdk.api_lib.dataproc import compute_helpers
from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _CommonArgs(parser, beta=False):
  """Register flags common to all tracks."""
  base.ASYNC_FLAG.AddToParser(parser)
  parser.add_argument('name', help='The name of this cluster.')
  clusters.ArgsForClusterRef(parser, beta)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a cluster."""

  detailed_help = {
      'EXAMPLES': """\
          To create a cluster, run:

            $ {command} my_cluster
      """
  }

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, beta=False)
    parser.add_argument(
        '--zone',
        '-z',
        help='The compute zone (e.g. us-central1-a) for the cluster.',
        action=actions.StoreProperty(properties.VALUES.compute.zone))

  @staticmethod
  def ValidateArgs(args):

    if args.single_node:
      # --num-workers and --num-preemptible-workers must be None (unspecified)
      # or 0
      if args.num_workers:
        raise exceptions.ConflictingArgumentsException(
            '--single-node', '--num-workers')
      if args.num_preemptible_workers:
        raise exceptions.ConflictingArgumentsException(
            '--single-node', '--num-preemptible-workers')

    if constants.ALLOW_ZERO_WORKERS_PROPERTY in args.properties:
      raise exceptions.InvalidArgumentException(
          '--properties',
          'Instead of %s, use gcloud beta dataproc clusters create '
          '--single-node to deploy single node clusters' %
          constants.ALLOW_ZERO_WORKERS_PROPERTY)

  def Run(self, args):
    self.ValidateArgs(args)

    dataproc = dp.Dataproc(self.ReleaseTrack())

    cluster_ref = util.ParseCluster(args.name, dataproc)

    compute_resources = compute_helpers.GetComputeResources(
        self.ReleaseTrack(), args.name)

    beta = self.ReleaseTrack() == base.ReleaseTrack.BETA
    cluster_config = clusters.GetClusterConfig(
        args, dataproc, cluster_ref.projectId, compute_resources, beta)

    cluster = dataproc.messages.Cluster(
        config=cluster_config,
        clusterName=cluster_ref.clusterName,
        projectId=cluster_ref.projectId)

    self.ConfigureCluster(dataproc.messages, args, cluster)

    operation = dataproc.client.projects_regions_clusters.Create(
        dataproc.messages.DataprocProjectsRegionsClustersCreateRequest(
            projectId=cluster_ref.projectId,
            region=cluster_ref.region,
            cluster=cluster,
            requestId=util.GetUniqueId()))

    if args.async:
      log.status.write(
          'Creating [{0}] with operation [{1}].'.format(
              cluster_ref, operation.name))
      return

    operation = util.WaitForOperation(
        dataproc,
        operation,
        message='Waiting for cluster creation operation',
        timeout_s=args.timeout)

    get_request = dataproc.messages.DataprocProjectsRegionsClustersGetRequest(
        projectId=cluster_ref.projectId,
        region=cluster_ref.region,
        clusterName=cluster_ref.clusterName)
    cluster = dataproc.client.projects_regions_clusters.Get(get_request)
    if cluster.status.state == (
        dataproc.messages.ClusterStatus.StateValueValuesEnum.RUNNING):

      zone_uri = cluster.config.gceClusterConfig.zoneUri
      zone_short_name = zone_uri.split('/')[-1]

      # Log the URL of the cluster
      log.CreatedResource(
          cluster_ref,
          # Also indicate which zone the cluster was placed in. This is helpful
          # if the server picked a zone (auto zone)
          details='Cluster placed in zone [{0}]'.format(zone_short_name))
    else:
      log.error('Create cluster failed!')
      if operation.details:
        log.error('Details:\n' + operation.details)
    return cluster

  @staticmethod
  def ConfigureCluster(messages, args, cluster):
    """Performs any additional configuration of the cluster."""
    cluster.labels = labels_util.ParseCreateArgs(args,
                                                 messages.Cluster.LabelsValue)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a cluster."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, beta=True)
    flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.BETA)
    parser.add_argument(
        '--zone',
        '-z',
        help="""
            The compute zone (e.g. us-central1-a) for the cluster. If empty,
            and --region is set to a value other than 'global', the server will
            pick a zone in the region.
            """,
        action=actions.StoreProperty(properties.VALUES.compute.zone))

    parser.add_argument(
        '--max-idle',
        type=arg_parsers.Duration(),
        help="""\
        The duration before cluster is auto-deleted after last job completes,
        such as "2h" or "1d".
        See $ gcloud topic datetimes for information on duration formats.
        """)

    auto_delete_group = parser.add_mutually_exclusive_group()
    auto_delete_group.add_argument(
        '--max-age',
        type=arg_parsers.Duration(),
        help="""\
        The lifespan of the cluster before it is auto-deleted, such as
        "2h" or "1d".
        See $ gcloud topic datetimes for information on duration formats.
        """)

    auto_delete_group.add_argument(
        '--expiration-time',
        type=arg_parsers.Datetime.Parse,
        help="""\
        The time when cluster will be auto-deleted, such as
        "2017-08-29T18:52:51.142Z". See $ gcloud topic datetimes for
        information on time formats.
        """)

    for instance_type in ('master', 'worker'):
      help_msg = """\
      Attaches accelerators (e.g. GPUs) to the {instance_type}
      instance(s).
      """.format(instance_type=instance_type)
      if instance_type == 'worker':
        help_msg += """
      Note:
      No accelerators will be attached to preemptible workers, because
      preemptible VMs do not support accelerators.
      """
      help_msg += """
      *type*::: The specific type (e.g. nvidia-tesla-k80 for nVidia Tesla
      K80) of accelerator to attach to the instances. Use 'gcloud compute
      accelerator-types list' to learn about all available accelerator
      types.

      *count*::: The number of pieces of the accelerator to attach to each
      of the instances. The default value is 1.
      """
      parser.add_argument(
          '--{0}-accelerator'.format(instance_type),
          type=arg_parsers.ArgDict(spec={
              'type': str,
              'count': int,
          }),
          metavar='type=TYPE,[count=COUNT]',
          help=help_msg)

  @staticmethod
  def ValidateArgs(args):
    super(CreateBeta, CreateBeta).ValidateArgs(args)
    if args.master_accelerator and 'type' not in args.master_accelerator:
      raise exceptions.InvalidArgumentException(
          '--master-accelerator', 'accelerator type must be specified. '
          'e.g. --master-accelerator type=nvidia-tesla-k80,count=2')
    if args.worker_accelerator and 'type' not in args.worker_accelerator:
      raise exceptions.InvalidArgumentException(
          '--worker-accelerator', 'accelerator type must be specified. '
          'e.g. --worker-accelerator type=nvidia-tesla-k80,count=2')
