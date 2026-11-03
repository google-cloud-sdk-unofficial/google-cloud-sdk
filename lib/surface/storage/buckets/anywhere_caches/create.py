# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implementation of create command for creating Anywhere Cache Instances."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.storage import anywhere_caches_util
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.buckets.anywhere_caches import create_anywhere_cache_task


def _add_common_args(parser):
  """Adds common arguments shared between GA and Alpha tracks."""
  parser.add_argument(
      'url',
      type=str,
      help=(
          'Specifies the URL of the bucket where the Anywhere Cache should be'
          ' created.'
      ),
  )

  parser.add_argument(
      'zone',
      type=str,
      nargs='+',
      help=(
          'Specifies the name of the zonal locations where the Anywhere Cache'
          ' should be created.'
      ),
  )

  parser.add_argument(
      '--ttl',
      type=arg_parsers.Duration(),
      help='Cache entry time-to-live. Default to 24h if not provided.',
  )

  flags.add_admission_policy_flag(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class Create(base.CreateCommand):
  """Create Anywhere Cache instances for a bucket."""

  hints = base.CommandHint(read_only=False)

  detailed_help = {
      'DESCRIPTION': """

      Create Anywhere Cache instances.
      Only one cache instance per zone can be created for each bucket.
      """,
      'EXAMPLES': """

      The following command creates an anywhere cache instance for bucket
      in ``asia-south2-b'' zone:

        $ {command} gs://my-bucket asia-south2-b

      The following command creates anywhere cache instances for bucket
      in ``asia-south2-b'', and ``asia-east1-a'' zone:

        $ {command} gs://my-bucket asia-south2-b asia-east1-a

      The following command creates an anywhere cache instance for bucket
      in ``asia-south2-b'' zone, with ttl for cache entry as 6 hours, and
      admission policy as ``ADMIT_ON_SECOND_MISS'':

        $ {command} gs://my-bucket asia-south2-b --ttl=6h --admission-policy='ADMIT_ON_SECOND_MISS'
      """,
  }

  @classmethod
  def Args(cls, parser):
    _add_common_args(parser)
    parser.add_argument(
        '--enable-ingest-on-write',
        action=arg_parsers.StoreTrueFalseAction,
        help='Enables the Ingest-on-Write feature on the bucket.',
    )

  def get_task_iterator(self, args, task_status_queue):
    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_bucket(args.command_path, url)

    progress_callbacks.workload_estimator_callback(
        task_status_queue, len(args.zone)
    )

    ttl = None
    if args.ttl is not None:
      ttl = str(args.ttl) + 's'

    for zone in args.zone:
      yield create_anywhere_cache_task.CreateAnywhereCacheTask(
          url,
          zone,
          admission_policy=args.admission_policy,
          ttl=ttl,
          enable_ingest_on_write=args.enable_ingest_on_write,
      )

  def Run(self, args):
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    task_iterator = self.get_task_iterator(args, task_status_queue)
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


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class CreateAlpha(Create):
  """Create Anywhere Cache instances for a bucket."""

  @classmethod
  def Args(cls, parser):
    _add_common_args(parser)
    # Ingest-on-write flags group requiring explicit enablement.
    ingest_on_write_group = parser.add_group(required=False)
    ingest_on_write_group.add_argument(
        '--enable-ingest-on-write',
        action=arg_parsers.StoreTrueFalseAction,
        required=True,
        help='Enables the Ingest-on-Write feature on the bucket.',
    )
    prefixes_group = ingest_on_write_group.add_mutually_exclusive_group(
        hidden=True,
    )
    prefixes_group.add_argument(
        '--ingest-on-write-prefixes',
        type=arg_parsers.ArgList(),
        metavar='PREFIX',
        hidden=True,
        help='Comma-separated list of prefixes to ingest on write.',
    )
    prefixes_group.add_argument(
        '--ingest-on-write-prefixes-file',
        type=str,
        metavar='FILE',
        hidden=True,
        help=(
            'Path to a local file with one prefix per line (# comments and'
            ' blank lines ignored) to ingest on write. Mutually exclusive with'
            ' --ingest-on-write-prefixes.'
        ),
    )

  def get_task_iterator(self, args, task_status_queue):
    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_bucket(args.command_path, url)

    raw_prefixes = getattr(args, 'ingest_on_write_prefixes', None)
    prefixes_file = getattr(args, 'ingest_on_write_prefixes_file', None)

    if not args.enable_ingest_on_write:
      if raw_prefixes is not None:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--no-enable-ingest-on-write',
            '--ingest-on-write-prefixes',
        )
      if prefixes_file is not None:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--no-enable-ingest-on-write',
            '--ingest-on-write-prefixes-file',
        )

    if raw_prefixes is not None:
      non_empty_raw = [prefix for prefix in raw_prefixes if prefix]
      prefixes = (
          anywhere_caches_util.normalize_and_validate_prefixes(non_empty_raw)
          if non_empty_raw
          else []
      )
    elif prefixes_file is not None:
      prefixes = anywhere_caches_util.read_and_validate_prefixes_file(
          prefixes_file
      )
    else:
      prefixes = None

    if prefixes:
      # Verify UBLA is enabled on bucket before mutating cache or folders.
      anywhere_caches_util.validate_ubla_for_bucket(url.bucket_name)
      # Anywhere Cache itself has ingestOnWrite=False when prefix IOW is used.
      enable_ingest_on_write = False
    elif prefixes is not None:
      # Empty prefixes list enables bucket-level ingest-on-write without
      # creating managed folders.
      enable_ingest_on_write = True
      prefixes = None
    else:
      enable_ingest_on_write = args.enable_ingest_on_write

    progress_callbacks.workload_estimator_callback(
        task_status_queue, len(args.zone)
    )

    ttl = None
    if args.ttl is not None:
      ttl = str(args.ttl) + 's'

    tasks = []
    for zone in args.zone:
      tasks.append(
          create_anywhere_cache_task.CreateAnywhereCacheTask(
              url,
              zone,
              admission_policy=args.admission_policy,
              ttl=ttl,
              enable_ingest_on_write=enable_ingest_on_write,
              ingest_on_write_prefixes=prefixes,
          )
      )
    return tasks
