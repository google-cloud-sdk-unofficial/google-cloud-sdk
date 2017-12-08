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

import argparse

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import utils as api_utils
from googlecloudsdk.api_lib.dataproc import compute_helpers
from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _CommonArgs(parser):
  """Register flags common to all tracks."""
  instances_flags.AddTagsArgs(parser)
  base.ASYNC_FLAG.AddToParser(parser)
  parser.add_argument(
      '--metadata',
      type=arg_parsers.ArgDict(min_length=1),
      action='append',
      default=None,
      help=('Metadata to be made available to the guest operating system '
            'running on the instances'),
      metavar='KEY=VALUE')
  parser.add_argument('name', help='The name of this cluster.')
  parser.add_argument(
      '--num-workers',
      type=int,
      help='The number of worker nodes in the cluster. Defaults to '
      'server-specified.')
  parser.add_argument(
      '--num-preemptible-workers',
      type=int,
      help='The number of preemptible worker nodes in the cluster.')
  parser.add_argument(
      '--master-machine-type',
      help='The type of machine to use for the master. Defaults to '
      'server-specified.')
  parser.add_argument(
      '--worker-machine-type',
      help='The type of machine to use for workers. Defaults to '
      'server-specified.')
  parser.add_argument('--image', help=argparse.SUPPRESS)
  parser.add_argument(
      '--image-version',
      metavar='VERSION',
      help='The image version to use for the cluster. Defaults to the '
      'latest version.')
  parser.add_argument(
      '--bucket',
      help='The Google Cloud Storage bucket to use with the Google Cloud '
      'Storage connector. A bucket is auto created when this parameter is '
      'not specified.')

  netparser = parser.add_mutually_exclusive_group()
  network = netparser.add_argument(
      '--network',
      help='Specifies the network that the cluster will be part of.')
  network.detailed_help = """\
      The Compute Engine network that the VM instances of the cluster will be
      part of. This is mutually exclusive with --subnet. If neither is
      specified, this defaults to the "default" network.
      """
  subnet = netparser.add_argument(
      '--subnet',
      help='Specifies the subnet that the cluster will be part of.')
  subnet.detailed_help = """\
      Specifies the subnet that the cluster will be part of. This is mutally
      exclusive with --network.
      """
  parser.add_argument(
      '--zone', '-z',
      help='The compute zone (e.g. us-central1-a) for the cluster.',
      action=actions.StoreProperty(properties.VALUES.compute.zone))
  parser.add_argument(
      '--num-worker-local-ssds',
      type=int,
      help='The number of local SSDs to attach to each worker in a cluster.')
  parser.add_argument(
      '--num-master-local-ssds',
      type=int,
      help='The number of local SSDs to attach to the master in a cluster.')
  parser.add_argument(
      '--initialization-actions',
      type=arg_parsers.ArgList(min_length=1),
      metavar='CLOUD_STORAGE_URI',
      help=('A list of Google Cloud Storage URIs of '
            'executables to run on each node in the cluster.'))
  parser.add_argument(
      '--initialization-action-timeout',
      type=arg_parsers.Duration(),
      metavar='TIMEOUT',
      default='10m',
      help='The maximum duration of each initialization action.')
  properties_parser = parser.add_argument(
      '--properties',
      type=arg_parsers.ArgDict(),
      metavar='PREFIX:PROPERTY=VALUE',
      default={},
      help='Specifies cluster configuration properties.')
  properties_parser.detailed_help = """\
Specifies configuration properties for installed packages, such as Hadoop
and Spark.

Properties are mapped to configuration files by specifying a prefix, such as
"core:io.serializations". The following are supported prefixes and their
mappings:

[format="csv",options="header"]
|========
Prefix,Target Configuration File
core,core-site.xml
hdfs,hdfs-site.xml
mapred,mapred-site.xml
yarn,yarn-site.xml
hive,hive-site.xml
pig,pig.properties
spark,spark-defaults.conf
|========

"""
  scope_parser = parser.add_argument(
      '--scopes',
      type=arg_parsers.ArgList(min_length=1),
      metavar='SCOPE',
      help="Specifies scopes for the node instances. The project's default "
      'service account is used.')
  scope_parser.detailed_help = """\
Specifies scopes for the node instances. The project's default service account
is used. Multiple SCOPEs can specified, separated by commas.
Examples:

  $ {{command}} example-cluster --scopes https://www.googleapis.com/auth/bigtable.admin

  $ {{command}} example-cluster --scopes sqlservice,bigquery

The following scopes necessary for the cluster to function properly are always
added, even if not explicitly specified:

[format="csv"]
|========
{minimum_scopes}
|========

If this flag is not specified the following default scopes are also included:

[format="csv"]
|========
{additional_scopes}
|========

If you want to enable all scopes use the 'cloud-platform' scope.

SCOPE can be either the full URI of the scope or an alias.
Available aliases are:

[format="csv",options="header"]
|========
Alias,URI
{aliases}
|========
""".format(
    minimum_scopes='\n'.join(constants.MINIMUM_SCOPE_URIS),
    additional_scopes='\n'.join(constants.ADDITIONAL_DEFAULT_SCOPE_URIS),
    aliases='\n'.join(
        ','.join(p) for p in sorted(compute_helpers.SCOPE_ALIASES.iteritems())))

  master_boot_disk = parser.add_mutually_exclusive_group()
  worker_boot_disk = parser.add_mutually_exclusive_group()

  master_boot_disk.add_argument(
      '--master-boot-disk-size-gb',
      type=int,
      help='DEPRECATED, use --master-boot-disk-size')
  worker_boot_disk.add_argument(
      '--worker-boot-disk-size-gb',
      type=int,
      help='DEPRECATED, use --worker-boot-disk-size')

  boot_disk_size_detailed_help = """\
      The size of the boot disk. The value must be a
      whole number followed by a size unit of ``KB'' for kilobyte, ``MB''
      for megabyte, ``GB'' for gigabyte, or ``TB'' for terabyte. For example,
      ``10GB'' will produce a 10 gigabyte disk. The minimum size a boot disk
      can have is 10 GB. Disk size must be a multiple of 1 GB.
      """
  master_boot_disk_size = master_boot_disk.add_argument(
      '--master-boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help='The size of the boot disk of the master in a cluster.')
  master_boot_disk_size.detailed_help = boot_disk_size_detailed_help
  worker_boot_disk_size = worker_boot_disk.add_argument(
      '--worker-boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help='The size of the boot disk of each worker in a cluster.')
  worker_boot_disk_size.detailed_help = boot_disk_size_detailed_help


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a cluster."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To create a cluster, run:

            $ {command} my_cluster
      """
  }

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

    # Available but hidden in GA track.
    parser.add_argument(
        '--preemptible-worker-boot-disk-size',
        type=arg_parsers.BinarySize(lower_bound='10GB'),
        help=argparse.SUPPRESS)

  @staticmethod
  def ValidateArgs(args):
    if args.master_boot_disk_size_gb:
      log.warn('The --master-boot-disk-size-gb flag is deprecated. '
               'Use equivalent --master-boot-disk-size=%sGB flag.',
               args.master_boot_disk_size_gb)

    if args.worker_boot_disk_size_gb:
      log.warn('The --worker-boot-disk-size-gb flag is deprecated. '
               'Use equivalent --worker-boot-disk-size=%sGB flag.',
               args.worker_boot_disk_size_gb)

  @util.HandleHttpError
  def Run(self, args):
    self.ValidateArgs(args)

    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    cluster_ref = util.ParseCluster(args.name, self.context)

    config_helper = compute_helpers.ConfigurationHelper.FromContext(
        self.context)
    compute_uris = config_helper.ResolveGceUris(
        args.name,
        args.image,
        args.master_machine_type,
        args.worker_machine_type,
        args.network,
        args.subnet)

    init_actions = []
    timeout_str = str(args.initialization_action_timeout) + 's'
    if args.initialization_actions:
      init_actions = [messages.NodeInitializationAction(
          executableFile=exe, executionTimeout=timeout_str)
                      for exe in args.initialization_actions]
    expanded_scopes = compute_helpers.ExpandScopeAliases(args.scopes)

    software_config = messages.SoftwareConfig(
        imageVersion=args.image_version)

    master_boot_disk_size_gb = args.master_boot_disk_size_gb
    if args.master_boot_disk_size:
      master_boot_disk_size_gb = (
          api_utils.BytesToGb(args.master_boot_disk_size))

    worker_boot_disk_size_gb = args.worker_boot_disk_size_gb
    if args.worker_boot_disk_size:
      worker_boot_disk_size_gb = (
          api_utils.BytesToGb(args.worker_boot_disk_size))

    preemptible_worker_boot_disk_size_gb = (
        api_utils.BytesToGb(args.preemptible_worker_boot_disk_size))

    if args.properties:
      software_config.properties = encoding.DictToMessage(
          args.properties, messages.SoftwareConfig.PropertiesValue)

    gce_cluster_config = messages.GceClusterConfig(
        networkUri=compute_uris['network'],
        subnetworkUri=compute_uris['subnetwork'],
        serviceAccountScopes=expanded_scopes,
        zoneUri=compute_uris['zone'])

    if args.tags:
      gce_cluster_config.tags = args.tags

    if args.metadata:
      flat_metadata = dict((k, v) for d in args.metadata for k, v in d.items())
      gce_cluster_config.metadata = encoding.DictToMessage(
          flat_metadata, messages.GceClusterConfig.MetadataValue)

    cluster_config = messages.ClusterConfig(
        configBucket=args.bucket,
        gceClusterConfig=gce_cluster_config,
        masterConfig=messages.InstanceGroupConfig(
            imageUri=compute_uris['image'],
            machineTypeUri=compute_uris['master_machine_type'],
            diskConfig=messages.DiskConfig(
                bootDiskSizeGb=master_boot_disk_size_gb,
                numLocalSsds=args.num_master_local_ssds,
            ),
        ),
        workerConfig=messages.InstanceGroupConfig(
            numInstances=args.num_workers,
            imageUri=compute_uris['image'],
            machineTypeUri=compute_uris['worker_machine_type'],
            diskConfig=messages.DiskConfig(
                bootDiskSizeGb=worker_boot_disk_size_gb,
                numLocalSsds=args.num_worker_local_ssds,
            ),
        ),
        initializationActions=init_actions,
        softwareConfig=software_config,
    )

    # Secondary worker group is optional.
    if args.num_preemptible_workers is not None:
      cluster_config.secondaryWorkerConfig = (
          messages.InstanceGroupConfig(
              numInstances=args.num_preemptible_workers,
              diskConfig=messages.DiskConfig(
                  bootDiskSizeGb=preemptible_worker_boot_disk_size_gb,
              )))

    cluster = messages.Cluster(
        config=cluster_config,
        clusterName=cluster_ref.clusterName,
        projectId=cluster_ref.projectId)

    operation = client.projects_regions_clusters.Create(
        messages.DataprocProjectsRegionsClustersCreateRequest(
            projectId=cluster_ref.projectId,
            region=cluster_ref.region,
            cluster=cluster))

    if args.async:
      log.status.write(
          'Creating [{0}] with operation [{1}].'.format(
              cluster_ref, operation.name))
      return

    operation = util.WaitForOperation(
        operation, self.context, 'Waiting for cluster creation operation')

    cluster = client.projects_regions_clusters.Get(cluster_ref.Request())
    if cluster.status.state == (
        messages.ClusterStatus.StateValueValuesEnum.RUNNING):
      log.CreatedResource(cluster_ref)
    else:
      log.error('Create cluster failed!')
      if operation.details:
        log.error('Details:\n' + operation.details)
    return cluster


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a cluster."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

    # Available and visible in Beta track.
    preemptible_worker_boot_disk_size = parser.add_argument(
        '--preemptible-worker-boot-disk-size',
        type=arg_parsers.BinarySize(lower_bound='10GB'),
        help='The size of the boot disk of each premptible worker in a '
             'cluster.')
    preemptible_worker_boot_disk_size.detailed_help = """\
        The size of the boot disk. The value must be a
        whole number followed by a size unit of ``KB'' for kilobyte, ``MB''
        for megabyte, ``GB'' for gigabyte, or ``TB'' for terabyte. For example,
        ``10GB'' will produce a 10 gigabyte disk. The minimum size a boot disk
        can have is 10 GB. Disk size must be a multiple of 1 GB.
        """
