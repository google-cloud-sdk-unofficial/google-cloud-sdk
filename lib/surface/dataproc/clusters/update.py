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

from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log


class Update(base.Command):
  """Update the number of worker nodes in a cluster."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To resize a cluster, run:

            $ {command} my_cluster --num-workers 5

          To change the number preemptible workers in a cluster, run:

            $ {command} my_cluster --num-preemptible-workers 5
          """,
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'name',
        help='The name of the cluster to update.')
    parser.add_argument(
        '--num-workers',
        type=int,
        help='The new number of worker nodes in the cluster.')
    parser.add_argument(
        '--num-preemptible-workers',
        type=int,
        help='The new number of preemptible worker nodes in the cluster.')
    # Leaving this option here since it was in public announcement.
    # Hiding it so new users see the preferred --num-workers
    # option in help.
    # TODO(user): remove before public beta launch.
    parser.add_argument(
        '--new-num-workers',
        type=int,
        help=argparse.SUPPRESS)

  @util.HandleHttpError
  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    cluster_ref = util.ParseCluster(args.name, self.context)

    cluster_config = messages.ClusterConfig()
    changed_fields = []

    has_changes = False

    if args.new_num_workers is not None:
      log.warn('--new-num-workers parameter is deprecated and will be removed '
               'in a future release. Please use --num-workers instead')
      args.num_workers = args.new_num_workers

    if args.num_workers is not None:
      worker_config = messages.InstanceGroupConfig(
          numInstances=args.num_workers)
      cluster_config.workerConfig = worker_config
      changed_fields.append('config.worker_config.num_instances')
      has_changes = True

    if args.num_preemptible_workers is not None:
      worker_config = messages.InstanceGroupConfig(
          numInstances=args.num_preemptible_workers)
      cluster_config.secondaryWorkerConfig = worker_config
      changed_fields.append(
          'config.secondary_worker_config.num_instances')
      has_changes = True

    if not has_changes:
      raise exceptions.ToolException(
          'Must specify at least one cluster parameter to update.')

    cluster = messages.Cluster(
        config=cluster_config,
        clusterName=cluster_ref.clusterName,
        projectId=cluster_ref.projectId)

    request = messages.DataprocProjectsRegionsClustersPatchRequest(
        clusterName=cluster_ref.clusterName,
        region=cluster_ref.region,
        projectId=cluster_ref.projectId,
        cluster=cluster,
        updateMask=','.join(changed_fields))

    operation = client.projects_regions_clusters.Patch(request)

    if args.async:
      log.status.write(
          'Updating [{0}] with operation [{1}].'.format(
              cluster_ref, operation.name))
      return

    util.WaitForOperation(
        operation,
        self.context,
        message='Waiting for cluster update operation',
        timeout_s=3600 * 3)

    cluster = client.projects_regions_clusters.Get(cluster_ref.Request())
    log.UpdatedResource(cluster_ref)
    return cluster
