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
"""Implementation of update command for Rapid Cache Ultra instances."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.buckets.rapid_caches import (
    patch_rapid_cache_task,
)


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update Rapid Cache Ultra instances."""

  detailed_help = {
      'DESCRIPTION': (
          """
      Update one or more Rapid Cache Ultra instances.
      """
      ),
      'EXAMPLES': (
          """
      The following command updates cache entry's ttl and admission policy of
      Rapid Cache Ultra instance ``my-bucket/my-cache-id'':

        $ {command} my-bucket/my-cache-id --ttl=6h \\
            --admission-policy=ADMIT_ON_SECOND_MISS

      The following command updates cache entry's ttl of Rapid Cache Ultra
      instances in ``bucket-1/cache-1'' and ``bucket-2/cache-2'':

        $ {command} bucket-1/cache-1 bucket-2/cache-2 --ttl=12h
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'id',
        type=str,
        nargs='+',
        help=(
            'Identifiers for Rapid Cache Ultra instances. They are'
            ' combination of bucket_name/cache_id. For example:'
            ' test-bucket/my-cache-id.'
        ),
    )
    flags.add_rapid_cache_flags(parser)
    flags.add_async_flag(parser)

  def _get_task_iterator(self, args, task_status_queue):
    progress_callbacks.workload_estimator_callback(
        task_status_queue, len(args.id)
    )

    ttl = str(args.ttl) + 's' if args.ttl is not None else None
    is_async = args.async_ if args.async_ is not None else True

    for id_str in args.id:
      bucket_name, _, rapid_cache_id = id_str.rpartition(
          storage_url.CLOUD_URL_DELIMITER
      )
      yield patch_rapid_cache_task.PatchRapidCacheTask(
          bucket_name,
          rapid_cache_id,
          admission_policy=args.admission_policy,
          ttl=ttl,
          is_async=is_async,
      )

  def Run(self, args):
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    task_iterator = self._get_task_iterator(args, task_status_queue)

    self.exit_code = task_executor.execute_tasks(
        task_iterator,
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER, manifest_path=None
        ),
    )
