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
"""Implementation of update command for updating Anywhere Cache instances."""

import collections

from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.storage import anywhere_caches_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.buckets.anywhere_caches import patch_anywhere_cache_task
from googlecloudsdk.core import exceptions as core_exceptions

_PREFIX_FLAGS_REQUIRING_ENABLE_INGEST_ON_WRITE = (
    '--ingest-on-write-prefixes',
    '--ingest-on-write-prefixes-file',
    '--add-ingest-on-write-prefixes',
    '--remove-ingest-on-write-prefixes',
)


def _add_common_args(parser):
  """Adds common arguments shared between GA and Alpha tracks."""
  parser.add_argument(
      'id',
      type=str,
      nargs='+',
      help=(
          'Identifiers for a Anywhere Cache Instance.They are combination of'
          ' bucket_name/anywhere_cache_id. For example :'
          ' test-bucket/my-cache-id.'
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
class Update(base.UpdateCommand):
  """Update Anywhere Cache instances."""

  hints = base.CommandHint(read_only=False)

  detailed_help = {
      'DESCRIPTION': """

      Update one or more Anywhere Cache instances. A cache instance can be
      updated if its state is created or pending creation.
      """,
      'EXAMPLES': """

      The following command updates cache entry's ttl, and admisson policy of
      anywhere cache instance in bucket ``my-bucket'' having anywhere_cache_id
      ``my-cache-id'':

        $ {command} my-bucket/my-cache-id --ttl=6h --admission-policy='ADMIT_ON_SECOND_MISS'

      The following command updates cache entry's ttl of anywhere cache
      instances in bucket ``bucket-1'' and ``bucket-2'' having anywhere_cache_id
      ``my-cache-id-1'', and ``my-cache-id-2'' respectively:

        $ {command} bucket-1/my-cache-id-1 bucket-2/my-cache-id-2 --ttl=6h
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
    progress_callbacks.workload_estimator_callback(
        task_status_queue, len(args.id)
    )

    ttl = str(args.ttl) + 's' if args.ttl else None

    for id_str in args.id:
      bucket_name, _, anywhere_cache_id = id_str.rpartition('/')
      yield patch_anywhere_cache_task.PatchAnywhereCacheTask(
          bucket_name,
          anywhere_cache_id,
          admission_policy=args.admission_policy,
          ttl=ttl,
          enable_ingest_on_write=args.enable_ingest_on_write,
      )

  def Run(self, args):
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    task_iterator = self.get_task_iterator(args, task_status_queue)

    self.exit_code = task_executor.execute_tasks(
        task_iterator,
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER, manifest_path=None
        ),
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class UpdateAlpha(Update):
  """Update Anywhere Cache instances."""

  @classmethod
  def Args(cls, parser):
    _add_common_args(parser)
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

    overwrite_group = prefixes_group.add_mutually_exclusive_group(hidden=True)
    overwrite_group.add_argument(
        '--ingest-on-write-prefixes',
        type=arg_parsers.ArgList(min_length=1),
        metavar='PREFIX',
        hidden=True,
        help='Comma-separated list of prefixes to ingest on write.',
    )
    overwrite_group.add_argument(
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
    overwrite_group.add_argument(
        '--clear-ingest-on-write-prefixes',
        action='store_true',
        hidden=True,
        help='Clears all prefix-level ingest-on-write configurations.',
    )

    incremental_group = prefixes_group.add_group(hidden=True)
    incremental_group.add_argument(
        '--add-ingest-on-write-prefixes',
        type=arg_parsers.ArgList(min_length=1),
        metavar='PREFIX',
        hidden=True,
        help='Comma-separated list of prefixes to add to ingest on write.',
    )
    incremental_group.add_argument(
        '--remove-ingest-on-write-prefixes',
        type=arg_parsers.ArgList(min_length=1),
        metavar='PREFIX',
        hidden=True,
        help='Comma-separated list of prefixes to remove from ingest on write.',
    )

  def _validate_ingest_on_write_args(self, args):
    """Validates ingest-on-write arguments."""
    if (
        not args.enable_ingest_on_write
        and args.enable_ingest_on_write is not None
    ):
      specified_flags = set(args.GetSpecifiedArgNames())
      conflicting_flags = [
          flag
          for flag in _PREFIX_FLAGS_REQUIRING_ENABLE_INGEST_ON_WRITE
          if flag in specified_flags
      ]
      if conflicting_flags:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--no-enable-ingest-on-write', *conflicting_flags
        )

  def _parse_prefix_args(self, args):
    overwrite_prefixes = None
    if args.ingest_on_write_prefixes is not None:
      overwrite_prefixes = anywhere_caches_util.normalize_and_validate_prefixes(
          args.ingest_on_write_prefixes
      )
    elif args.ingest_on_write_prefixes_file is not None:
      overwrite_prefixes = anywhere_caches_util.read_and_validate_prefixes_file(
          args.ingest_on_write_prefixes_file
      )
      if not overwrite_prefixes:
        raise calliope_exceptions.InvalidArgumentException(
            '--ingest-on-write-prefixes-file',
            'Prefixes file must contain at least one prefix. Use'
            ' --clear-ingest-on-write-prefixes to clear all prefixes.',
        )
    elif args.clear_ingest_on_write_prefixes:
      overwrite_prefixes = []

    add_prefixes = None
    if args.add_ingest_on_write_prefixes is not None:
      add_prefixes = anywhere_caches_util.normalize_and_validate_prefixes(
          args.add_ingest_on_write_prefixes
      )

    remove_prefixes = None
    if args.remove_ingest_on_write_prefixes is not None:
      remove_prefixes = anywhere_caches_util.normalize_and_validate_prefixes(
          args.remove_ingest_on_write_prefixes
      )

    if (
        add_prefixes
        and remove_prefixes
        and not set(add_prefixes).isdisjoint(remove_prefixes)
    ):
      raise calliope_exceptions.ConflictingArgumentsException(
          '--add-ingest-on-write-prefixes',
          '--remove-ingest-on-write-prefixes',
      )

    return overwrite_prefixes, add_prefixes, remove_prefixes

  def _group_caches_by_bucket(self, cache_identifiers):
    caches_by_bucket = collections.defaultdict(list)
    for id_str in cache_identifiers:
      bucket_name, _, cache_id = id_str.rpartition('/')
      caches_by_bucket[bucket_name].append(cache_id)
    return caches_by_bucket

  def _get_existing_enabled_by_bucket(self, caches_by_bucket):
    existing_enabled_by_bucket = {}
    for bucket_name, cache_ids in caches_by_bucket.items():
      try:
        existing_enabled_by_bucket[bucket_name] = (
            anywhere_caches_util.get_enabled_managed_folder_prefixes(
                bucket_name, cache_ids, short_circuit=False
            )
        )
      except api_errors.GcsApiError as e:
        status_code = getattr(e, 'status_code', None) or getattr(
            getattr(e, 'payload', None), 'status_code', None
        )
        if status_code == 403:
          raise core_exceptions.Error(
              'PERMISSION_DENIED: Caller lacks'
              " 'storage.managedFolders.list' permission on bucket"
              ' [gs://{}] required to overwrite or clear prefix-level'
              ' ingest-on-write configurations.'.format(bucket_name)
          )
        raise
    return existing_enabled_by_bucket

  def _get_cache_ingest_on_write_args(
      self,
      args,
      overwrite_prefixes,
      add_prefixes,
      remove_prefixes,
      existing_enabled_prefixes,
  ):
    if overwrite_prefixes is not None:
      if overwrite_prefixes:
        bucket_enable_iow = False
        prefixes_to_enable = overwrite_prefixes
      else:
        bucket_enable_iow = args.enable_ingest_on_write
        prefixes_to_enable = None

      desired_prefixes_set = set(overwrite_prefixes)
      prefixes_to_disable = [
          prefix
          for prefix in existing_enabled_prefixes
          if prefix not in desired_prefixes_set
      ]
      return (
          bucket_enable_iow,
          prefixes_to_enable,
          prefixes_to_disable or None,
      )

    if add_prefixes is not None or remove_prefixes is not None:
      return False, add_prefixes, remove_prefixes

    return args.enable_ingest_on_write, None, None

  def get_task_iterator(self, args, task_status_queue):
    self._validate_ingest_on_write_args(args)
    overwrite_prefixes, add_prefixes, remove_prefixes = self._parse_prefix_args(
        args
    )

    caches_by_bucket = self._group_caches_by_bucket(args.id)
    has_prefix_updates = (
        overwrite_prefixes is not None
        or add_prefixes is not None
        or remove_prefixes is not None
    )
    if has_prefix_updates:
      for bucket_name in caches_by_bucket:
        anywhere_caches_util.validate_ubla_for_bucket(bucket_name)

    existing_enabled_by_bucket = {}
    if overwrite_prefixes is not None:
      existing_enabled_by_bucket = self._get_existing_enabled_by_bucket(
          caches_by_bucket
      )

    progress_callbacks.workload_estimator_callback(
        task_status_queue, len(args.id)
    )
    ttl = f'{args.ttl}s' if args.ttl else None

    tasks = []
    for id_str in args.id:
      bucket_name, _, anywhere_cache_id = id_str.rpartition('/')
      existing_enabled_prefixes = existing_enabled_by_bucket.get(
          bucket_name, {}
      ).get(anywhere_cache_id, [])
      bucket_enable_iow, prefixes_to_enable, prefixes_to_disable = (
          self._get_cache_ingest_on_write_args(
              args,
              overwrite_prefixes,
              add_prefixes,
              remove_prefixes,
              existing_enabled_prefixes,
          )
      )
      tasks.append(
          patch_anywhere_cache_task.PatchAnywhereCacheTask(
              bucket_name,
              anywhere_cache_id,
              admission_policy=args.admission_policy,
              ttl=ttl,
              enable_ingest_on_write=bucket_enable_iow,
              prefixes_to_enable=prefixes_to_enable,
              prefixes_to_disable=prefixes_to_disable,
          )
      )
    return tasks
