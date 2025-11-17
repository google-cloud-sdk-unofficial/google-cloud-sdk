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
"""Command to migrate an environment."""

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import operations_util as operations_api_util
from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import flags
from googlecloudsdk.command_lib.composer import image_versions_util as image_versions_command_util
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import log
import six


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Migrate(base.Command):
  """Migrates an environment from Composer 2 to Composer 3 in-place.

  If run asynchronously with `--async`, exits after printing an operation
  that can be used to poll the status of the creation operation via:

    {top_command} composer operations describe
  """

  @classmethod
  def Args(cls, parser):
    resource_args.AddEnvironmentResourceArg(parser, 'to migrate')
    base.ASYNC_FLAG.AddToParser(parser)

    target_version_type = arg_parsers.RegexpValidator(
        r'^composer-3-airflow-(\d+(?:\.\d+(?:\.\d+(?:-build\.\d+)?)?)?)',
        "must be in the form 'composer-3-airflow-X[.Y[.Z]]' For example:"
        " 'composer-3-airflow-2.3.4-build.5'. Only migrations to Composer 3 are"
        " supported.",
    )

    parser.add_argument(
        '--image-version',
        type=target_version_type,
        metavar='IMAGE_VERSION',
        required=True,
        help="""\
        Migrate the Composer 2 environment to this Composer 3 version in-place.

        The image version encapsulates the versions of both Cloud Composer and
        Apache Airflow. Must be of the form
        `composer-3-airflow-X[.Y[.Z[-build.N]]]`, where `[]` denotes optional
        fragments.

        Examples: `composer-3-airflow-2`, `composer-3-airflow-2.2`,
        `composer-3-airflow-2.3.4`, `composer-3-airflow-2.3.4-build.5`.

        The Cloud Composer portion of the image version must be a Composer 3
        version. The Apache Airflow portion of the image version can be a
        semantic version or an alias in the form of major or major.minor
        version numbers, resolved to the latest matching Apache Airflow version
        supported in the given Cloud Composer version. The resolved versions are
        stored in the migrated environment.
        """,
    )

    gke_cluster_retention_policy_group = parser.add_mutually_exclusive_group(
        help=(
            'Specify what should happen to the Composer 2 GKE cluster after'
            ' migration. If cluster is retained, until deleted manually it will'
            ' contribute to enviornment\'s cost.'
        ),
        required=True,
    )
    gke_cluster_retention_policy_group.add_argument(
        '--retain-gke-cluster',
        action='store_true',
        help='Retain Composer 2 GKE cluster after migration.',
    )
    gke_cluster_retention_policy_group.add_argument(
        '--delete-gke-cluster',
        action='store_true',
        help='Delete Composer 2 GKE cluster after migration.',
    )

    maintenance_window_group = parser.add_argument_group(
        help=(
            'Specify the maintenance window for the migrated environment. It'
            ' will override the current maintenance window. If not specified,'
            ' and the enviornment uses Composer 2 default maintenance window,'
            ' the migrated environment will use the Composer 3 default'
            ' maintenance window.'
        )
    )
    flags.MAINTENANCE_WINDOW_START_FLAG.AddToParser(maintenance_window_group)
    flags.MAINTENANCE_WINDOW_END_FLAG.AddToParser(maintenance_window_group)
    flags.MAINTENANCE_WINDOW_RECURRENCE_FLAG.AddToParser(
        maintenance_window_group
    )

    dag_processor_group = parser.add_argument_group(
        required=True,
        help=(
            'Specify the configuration of DAG processor for the'
            ' Composer 3 environment.'
        )
    )
    dag_processor_group.add_argument(
        '--dag-processor-cpu',
        type=float,
        required=True,
        help='CPU allocated to Airflow dag processor'
    )
    dag_processor_group.add_argument(
        '--dag-processor-memory',
        type=arg_parsers.BinarySize(
            lower_bound='1GB',
            upper_bound='128GB',
            suggested_binary_size_scales=['MB', 'GB'],
            default_unit='G',
        ),
        required=True,
        help=(
            'Memory allocated to Airflow dag processor, ex. 1GB, 3GB, 2. If'
            ' units are not provided, defaults to GB.'
        ),
    )
    dag_processor_group.add_argument(
        '--dag-processor-storage',
        type=arg_parsers.BinarySize(
            default_unit='G',
        ),
        required=True,
        help=(
            'Storage allocated to Airflow dag processor, ex. 600MB, 3GB, 2. If'
            ' units are not provided, defaults to GB.'
        ),
    )
    dag_processor_group.add_argument(
        '--dag-processor-count',
        type=int,
        required=True,
        help='Number of dag processors',
    )

    scheduler_group = parser.add_argument_group(
        help=(
            'Group of arguments for setting scheduler configuration in migrated'
            ' Composer environment. If not specified, the current scheduler'
            ' configuration will be preserved.'
        )
    )
    flags.SCHEDULER_CPU.AddToParser(scheduler_group)
    flags.SCHEDULER_MEMORY.AddToParser(scheduler_group)
    flags.SCHEDULER_STORAGE.AddToParser(scheduler_group)
    flags.NUM_SCHEDULERS.AddToParser(scheduler_group)

    worker_group = parser.add_argument_group(
        help=(
            'Group of arguments for setting worker configuration in migrated'
            ' Composer environment. If not specified, the current worker'
            ' configuration will be preserved.'
        )
    )
    flags.WORKER_CPU.AddToParser(worker_group)
    flags.WORKER_MEMORY.AddToParser(worker_group)
    flags.WORKER_STORAGE.AddToParser(worker_group)
    flags.MIN_WORKERS.AddToParser(worker_group)
    flags.MAX_WORKERS.AddToParser(worker_group)

    web_server_group = parser.add_argument_group(
        help=(
            'Group of arguments for setting web server configuration in'
            ' migrated Composer environment. If not specified, the current web'
            ' server configuration will be preserved.'
        )
    )
    flags.WEB_SERVER_CPU.AddToParser(web_server_group)
    flags.WEB_SERVER_MEMORY.AddToParser(web_server_group)
    flags.WEB_SERVER_STORAGE.AddToParser(web_server_group)

    triggerer_group = parser.add_argument_group(
        help=(
            'Group of arguments for setting triggerer configuration in migrated'
            ' Composer environment. If not specified, the current triggerer'
            ' configuration will be preserved.'
        )
    )
    flags.TRIGGERER_CPU.AddToParser(triggerer_group)
    flags.TRIGGERER_MEMORY.AddToParser(triggerer_group)
    flags.TRIGGERER_COUNT.AddToParser(triggerer_group)

  def _Validate(self, env_obj, args):
    if not image_versions_command_util.IsImageVersionStringComposerV2(
        env_obj.config.softwareConfig.imageVersion
    ) or not image_versions_command_util.IsImageVersionStringComposerV3(
        args.image_version
    ):
      raise command_util.InvalidUserInputError(
          'Migration is only supported from Composer 2 to Composer 3.'
      )

  def _ConstructGkeClusterRetentionPolicy(self, args, release_track):
    messages = api_util.GetMessagesModule(release_track=release_track)
    if args.retain_gke_cluster:
      return (
          messages.MigrateEnvironmentRequest.GkeClusterRetentionPolicyValueValuesEnum.RETAIN_GKE_CLUSTER
      )
    elif args.delete_gke_cluster:
      return (
          messages.MigrateEnvironmentRequest.GkeClusterRetentionPolicyValueValuesEnum.DELETE_GKE_CLUSTER
      )
    else:
      raise command_util.InvalidUserInputError(
          'One of --retain-gke-cluster or --delete-gke-cluster must be'
          ' specified.'
      )

  def _ConstructMigrateEnvironmentRequest(self, args, release_track):
    messages = api_util.GetMessagesModule(release_track=release_track)
    workloads_config = dict(
        dagProcessor=messages.DagProcessorResource(
            cpu=args.dag_processor_cpu,
            memoryGb=environments_api_util.MemorySizeBytesToGB(
                args.dag_processor_memory
            ),
            storageGb=environments_api_util.MemorySizeBytesToGB(
                args.dag_processor_storage
            ),
            count=args.dag_processor_count,
        ),
    )
    if (
        args.scheduler_cpu
        or args.scheduler_memory
        or args.scheduler_storage
        or args.scheduler_count
    ):
      workloads_config['scheduler'] = messages.SchedulerResource(
          cpu=args.scheduler_cpu,
          memoryGb=environments_api_util.MemorySizeBytesToGB(
              args.scheduler_memory
          ),
          storageGb=environments_api_util.MemorySizeBytesToGB(
              args.scheduler_storage
          ),
          count=args.scheduler_count,
      )
    if (
        args.worker_cpu
        or args.worker_memory
        or args.worker_storage
        or args.min_workers
        or args.max_workers
    ):
      workloads_config['worker'] = messages.WorkerResource(
          cpu=args.worker_cpu,
          memoryGb=environments_api_util.MemorySizeBytesToGB(
              args.worker_memory
          ),
          storageGb=environments_api_util.MemorySizeBytesToGB(
              args.worker_storage
          ),
          minCount=args.min_workers,
          maxCount=args.max_workers,
      )
    if args.web_server_cpu or args.web_server_memory or args.web_server_storage:
      workloads_config['webServer'] = messages.WebServerResource(
          cpu=args.web_server_cpu,
          memoryGb=environments_api_util.MemorySizeBytesToGB(
              args.web_server_memory
          ),
          storageGb=environments_api_util.MemorySizeBytesToGB(
              args.web_server_storage
          ),
      )
    if args.triggerer_cpu or args.triggerer_memory or args.triggerer_count:
      workloads_config['triggerer'] = messages.TriggererResource(
          cpu=args.triggerer_cpu,
          memoryGb=environments_api_util.MemorySizeBytesToGB(
              args.triggerer_memory
          ),
          count=args.triggerer_count,
      )

    migrate_request = dict(
        imageVersion=args.image_version,
        workloadsConfig=messages.WorkloadsConfig(**workloads_config),
        gkeClusterRetentionPolicy=self._ConstructGkeClusterRetentionPolicy(
            args, release_track
        ),
    )
    if (
        args.maintenance_window_start
        and args.maintenance_window_end
        and args.maintenance_window_recurrence
    ):
      migrate_request['maintenanceWindow'] = messages.MaintenanceWindow(
          startTime=args.maintenance_window_start.isoformat(),
          endTime=args.maintenance_window_end.isoformat(),
          recurrence=args.maintenance_window_recurrence,
      )
    return messages.MigrateEnvironmentRequest(**migrate_request)

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()
    env_obj = environments_api_util.Get(
        env_ref, release_track=self.ReleaseTrack())
    self._Validate(env_obj, args)

    request = self._ConstructMigrateEnvironmentRequest(
        args, self.ReleaseTrack()
    )
    operation = environments_api_util.Migrate(
        environment_ref=env_ref,
        request=request,
        release_track=self.ReleaseTrack(),
    )

    if args.async_:
      log.UpdatedResource(
          env_ref.RelativeName(),
          kind='environment',
          is_async=True,
          details='with operation [{0}]'.format(operation.name),
      )
      return operation
    try:
      operations_api_util.WaitForOperation(
          operation,
          'Waiting for [{}] to be updated with [{}]'.format(
              env_ref.RelativeName(), operation.name),
          release_track=self.ReleaseTrack())
    except command_util.Error as e:
      raise command_util.Error('Error updating [{}]: {}'.format(
          env_ref.RelativeName(), six.text_type(e)))
