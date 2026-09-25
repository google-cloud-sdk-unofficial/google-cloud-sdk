# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Implementation of create command for Rapid Cache Ultra instances."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.buckets.rapid_caches import (
    create_rapid_cache_task,
)


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create Rapid Cache Ultra instances for a bucket."""

  detailed_help = {
      'DESCRIPTION': (
          """
      Create Rapid Cache Ultra instances.
      Only one cache instance per zone can be created for each bucket.
      """
      ),
      'EXAMPLES': (
          """
      The following command creates a Rapid Cache Ultra instance for bucket
      ``gs://my-bucket'' in ``us-central1-a'' zone:

        $ {command} gs://my-bucket us-central1-a --cache-type=rapid-cache-ultra

      The following command creates Rapid Cache Ultra instances for bucket
      in ``us-central1-a'' and ``us-central1-b'' zones with ttl of 6 hours and
      admission policy as ``admit-on-second-miss'':

        $ {command} gs://my-bucket us-central1-a us-central1-b \\
            --cache-type=rapid-cache-ultra --ttl=6h \\
            --admission-policy=admit-on-second-miss
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'url',
        type=str,
        help=(
            'Specifies the URL of the bucket where the Rapid Cache Ultra'
            ' instance should be created.'
        ),
    )
    parser.add_argument(
        'zone',
        type=str,
        nargs='+',
        help=(
            'Specifies the name of the zonal locations where the Rapid Cache'
            ' Ultra instance should be created.'
        ),
    )
    parser.add_argument(
        '--cache-type',
        required=True,
        choices=['rapid-cache-ultra'],
        help='Specifies the type of cache to create.',
    )
    flags.add_rapid_cache_flags(parser)
    flags.add_async_flag(parser)

  def _get_task_iterator(self, args, task_status_queue):
    bucket_url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_bucket(args.command_path, bucket_url)

    progress_callbacks.workload_estimator_callback(
        task_status_queue, len(args.zone)
    )

    ttl = str(args.ttl) + 's' if args.ttl is not None else None
    is_async = args.async_ if args.async_ is not None else True

    for zone in args.zone:
      yield create_rapid_cache_task.CreateRapidCacheTask(
          bucket_url,
          zone,
          cache_type=args.cache_type,
          admission_policy=args.admission_policy,
          ttl=ttl,
          is_async=is_async,
      )

  def Run(self, args):
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    task_iterator = self._get_task_iterator(args, task_status_queue)
    plurality_checkable_task_iterator = (
        plurality_checkable_iterator.PluralityCheckableIterator(task_iterator)
    )
    self.exit_code = task_executor.execute_tasks(
        plurality_checkable_task_iterator,
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER, manifest_path=None
        ),
    )
