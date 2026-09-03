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

"""Command to create a cluster-director cluster resource."""

import textwrap

from googlecloudsdk.api_lib.hypercomputecluster import utils as api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cluster_director.clusters import flags
from googlecloudsdk.command_lib.cluster_director.clusters import utils
from googlecloudsdk.core import log


DETAILED_HELP = {
    "DESCRIPTION": textwrap.dedent("""
        *{command}* facilitates the creation of a cluster resource.

        Use one of the following options to create a cluster:
        - [Preferred] Use granular flags to define cluster specs.
        - Use --config flag with cluster specs in JSON format.
        - Use --quickstart-cluster or --reference-architecture to apply pre-configured templates.

        ## QUICKSTART CLUSTER AND REFERENCE ARCHITECTURES
        Quickstart cluster and reference architectures allow you to quickly provision clusters with pre-defined configurations for compute, storage, and orchestrator.

        *quickstart* (applied when using `--quickstart-cluster`):
        - Compute: 2x a3-megagpu-8g nodes (Flex Start, max duration 7 days).
        - Login Node: 1x n2-standard-16 node.
        - Storage: 36TB Lustre storage (scratch disk).

        *a3-ultra* (applied when using `--reference-architecture=a3-ultra`):
        - Compute: 4x reserved nodes (requires specifying `--reserved-instances`).
        - Login Node: 1x n2-standard-16 node.
        - Storage: 36TB Lustre storage (scratch disk) and 5.1TB Filestore storage.

        *a4-high-flex-start* (applied when using `--reference-architecture=a4-high-flex-start`):
        - Compute: 4x a4-highgpu-8g nodes (Flex Start, max duration 7 days).
        - Login Node: 1x n2-standard-16 node.
        - Storage: 18TB Lustre storage (scratch disk) and 2TB Filestore storage.

        *a4x-high* (applied when using `--reference-architecture=a4x-high`):
        - Compute: 18x reserved nodes (requires specifying `--reserved-instances`).
        - Login Node: 1x n2-standard-16 node.
        - Storage: 36TB Lustre storage (scratch disk).

        *g4-flex-start* (applied when using `--reference-architecture=g4-flex-start`):
        - Compute: 4x g4-standard-384 nodes (Flex Start, max duration 7 days).
        - Login Node: 1x n2-standard-16 node.
        - Storage: 36TB Lustre storage (scratch disk) and 10.2TB Filestore storage.

        *h4d-highmem-flex-start* (applied when using `--reference-architecture=h4d-highmem-flex-start`):
        - Compute: 4x h4d-highmem-192 nodes (Flex Start, max duration 7 days).
        - Login Node: 1x n2-standard-16 node.
        - Storage: 18TB Lustre storage (scratch disk) and 1TB Filestore storage.

        Please refer to the examples below for more details.
        """),
    "EXAMPLES": textwrap.dedent("""
        To create a cluster `my-cluster` in location `us-central1` with granular flags, run the following example:

        $ {command} my-cluster --location us-central1 \
        --description "My cluster description" \
        --labels env=prod,client=gcloud-cli \
        --create-network name=network0 \
        --create-filestores name=locations/us-central1-a/instances/filestore0,tier=ZONAL,capacityGb={filestoreSize},fileshare={fileshare} \
        --filestores locations/us-central1-a/instances/filestore1 \
        --create-buckets name=bucket0 \
        --buckets bucket1 \
        --create-lustres name=locations/us-central1-a/instances/lustre0,capacityGb={lustreSize},filesystem={filesystem} \
        --lustres locations/us-central1-a/instances/lustre1 \
        --reserved-instances id=compute0,reservation=zones/us-central1-a/reservations/{reservation} \
        --slurm-login-node machineType={machineType},zone=us-central1-a \
        --slurm-node-sets id=nodeset0,computeId=compute0 \
        --slurm-partitions id=partition0,nodesetIds=[nodeset0] \
        --slurm-default-partition partition0 \
        --format json

        To create a cluster `my-cluster` in location `us-central1` with config in JSON string format run the following example:

        $ {command} my-cluster --location=us-central1 --config='{"key": "value"}'

        Or create a JSON file `my-cluster-config.json` with the cluster specs and run the following file example:

        $ {command} my-cluster --location=us-central1 --config=my-cluster-config.json

        To create a cluster `my-cluster` in location `us-central1` using the quickstart setup with default cluster parameters, run the following example:

        $ {command} my-cluster --location=us-central1 --quickstart-cluster --create-network name=network0

        To create a cluster `my-cluster` in location `us-central1` using a pre-defined reference architecture choice (such as `g4-flex-start`), run the following example:

        $ {command} my-cluster --location=us-central1 --reference-architecture=g4-flex-start --create-network name=network0
        """),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Creates a Cluster Director resource."""

  @classmethod
  def Args(cls, parser):
    """Specifies command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    api_version = api_utils.GetApiVersion(cls.ReleaseTrack())
    utils.AddClusterNameArgToParser(parser=parser, api_version=api_version)
    group = parser.add_group(
        help="Cluster configuration for provisioning.",
        mutex=True,
        required=True,
    )
    flags.AddConfig(parser=group, api_version=api_version)
    flag_group = group.add_group(
        help="Flag Configurations to define cluster spec.",
    )
    flags.AddDescription(parser=flag_group, api_version=api_version)
    flags.AddLabels(parser=flag_group, api_version=api_version)
    network_group = flag_group.add_group(
        mutex=True,
        required=False,
        help="Network configuration for the cluster.",
    )
    flags.AddCreateNetwork(parser=network_group, api_version=api_version)
    network_source_group = network_group.add_group(
        help="Use an existing network source for the cluster.",
    )
    flags.AddNetworkSource(
        parser=network_source_group, api_version=api_version, required=True
    )
    flags.AddSubnetSource(
        parser=network_source_group, api_version=api_version, required=True
    )
    flags.AddNetworkProject(
        parser=network_source_group, api_version=api_version
    )
    ref_arch_group = flag_group.add_group(mutex=True)
    flags.AddReferenceArchitecture(
        parser=ref_arch_group, api_version=api_version
    )
    flags.AddQuickstartCluster(parser=ref_arch_group)
    flags.AddCreateFilestores(parser=flag_group, api_version=api_version)
    flags.AddFilestores(parser=flag_group, api_version=api_version)
    flags.AddCreateGcsBuckets(parser=flag_group, api_version=api_version)
    flags.AddGcsBuckets(parser=flag_group, api_version=api_version)
    flags.AddCreateLustres(parser=flag_group, api_version=api_version)
    flags.AddLustres(parser=flag_group, api_version=api_version)
    flags.AddOnDemandInstances(parser=flag_group, api_version=api_version)
    flags.AddSpotInstances(parser=flag_group, api_version=api_version)
    flags.AddReservedInstances(parser=flag_group, api_version=api_version)
    flags.AddFlexStartInstances(parser=flag_group, api_version=api_version)
    flags.AddSlurmLoginNode(
        parser=flag_group, api_version=api_version, required=False
    )
    flags.AddSlurmNodeSets(parser=flag_group, api_version=api_version)
    flags.AddSlurmPartitions(parser=flag_group, api_version=api_version)
    flags.AddSlurmDefaultPartition(parser=flag_group, api_version=api_version)
    flags.AddSlurmPrologBashScripts(parser=flag_group, api_version=api_version)
    flags.AddSlurmEpilogBashScripts(parser=flag_group, api_version=api_version)
    if api_version == "v1alpha":
      flags.AddSlurmTaskPrologBashScripts(
          parser=flag_group, api_version=api_version
      )
      flags.AddSlurmTaskEpilogBashScripts(
          parser=flag_group, api_version=api_version
      )
      flags.AddSlurmConfig(parser=flag_group, api_version=api_version)
      flags.AddSlurmDisableHealthCheckProgram(
          parser=flag_group, api_version=api_version
      )

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """
    release_track = self.ReleaseTrack()
    client = api_utils.GetClientInstance(release_track)
    messages = api_utils.GetMessagesModule(release_track)
    cluster_util = utils.ClusterUtil(args=args, message_module=messages)
    cluster_ref = cluster_util.cluster_ref

    if args.IsSpecified("config"):
      cluster = cluster_util.MakeClusterFromConfig()
    else:
      cluster = cluster_util.MakeCluster()

    operation = client.projects_locations_clusters.Create(
        messages.HypercomputeclusterProjectsLocationsClustersCreateRequest(
            parent=cluster_ref.Parent().RelativeName(),
            clusterId=cluster_ref.Name(),
            cluster=cluster,
        )
    )
    log.status.Print(
        "Create request issued for: [{0}]".format(cluster_ref.Name())
    )
    if args.async_:
      return operation

    response = api_utils.WaitForOperation(
        client=client,
        operation=operation,
        message="Waiting for operation [{0}] to complete".format(
            operation.name
        ),
        max_wait_sec=7200,
    )
    log.status.Print("Created cluster [{0}].".format(cluster_ref.Name()))
    return response


Create.detailed_help = DETAILED_HELP
