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
"""Implementation of Unix-like cat command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import stdin_iterator
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.objects import bulk_restore_objects_task
from googlecloudsdk.command_lib.storage.tasks.objects import restore_object_task


def _restore_task_iterator(args):
  """Yields restore tasks."""
  if args.preserve_acl:
    fields_scope = cloud_api.FieldsScope.FULL
  else:
    fields_scope = cloud_api.FieldsScope.SHORT
  user_request_args = (
      user_request_args_factory.get_user_request_args_from_command_args(
          args, metadata_type=user_request_args_factory.MetadataType.OBJECT
      )
  )
  for url_string in stdin_iterator.get_urls_iterable(
      args.urls, args.read_paths_from_stdin
  ):
    url = storage_url.storage_url_from_string(url_string)
    errors_util.raise_error_if_not_gcs(args.command_path, url)
    if args.asyncronous:
      yield bulk_restore_objects_task.BulkRestoreObjectsTask(
          url,
          allow_overwrite=args.allow_overwrite,
          deleted_after_time=args.deleted_after_time,
          deleted_before_time=args.deleted_before_time,
          user_request_args=user_request_args,
      )
    else:
      for resource in wildcard_iterator.get_wildcard_iterator(
          url_string, fields_scope=fields_scope
      ):
        yield restore_object_task.RestoreObjectTask(resource, user_request_args)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Restore(base.Command):
  """Restore one or more objects."""

  # TODO(b/292075826): Update docstring and help once bucket restore supported.
  detailed_help = {
      'DESCRIPTION': """
      The restore command restores soft-deleted objects:

        $ {command} restore url...

      """,
      'EXAMPLES': """

      Restore latest version of object in a bucket:

        $ {command} gs://bucket/file1.txt

      Restore specific version of object in a bucket:

        $ {command} gs://bucket/file1.txt#123

      Restore two objects in a bucket:

        $ {command} gs://bucket/file1.txt gs://bucket/file2.txt

      Restore all text objects in a bucket:

        $ {command} gs://bucket/**.txt

      Read list of files to restore from stdin:

        $ cat list-of-files.txt | {command} --read-paths-from-stdin

      Restore object with its original ACL policy:

        $ {command} gs://bucket/file1.txt --preserve-acl

      Restore all objects in a bucket asynchronously:

        $ {command} gs://bucket --async

      Restore all text files in a bucket asynchronously:

        $ {command} gs://bucket/**.txt --async

      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('urls', nargs='*', help='The url of objects to list.')
    flags.add_precondition_flags(parser)
    flags.add_preserve_acl_flag(parser)
    flags.add_read_paths_from_stdin_flag(parser)

    parser.add_argument(
        '--async',
        # Can't create `async` attribute because "async" is a keyword.
        dest='asyncronous',
        action='store_true',
        help=(
            'Initiates an asynchronous bulk restore operation on the specified'
            ' bucket.'
        ),
    )
    bulk_restore_flag_group = parser.add_group(help='BULK RESTORE OPTIONS')
    bulk_restore_flag_group.add_argument(
        '--allow-overwrite',
        action='store_true',
        help=(
            'If included, live objects will be overwritten. If versioning is'
            ' enabled, this will result in a noncurrent object. If versioning'
            ' is not enabled, this will result in a soft-deleted object.'
        ),
    )
    bulk_restore_flag_group.add_argument(
        '--deleted-after-time',
        type=arg_parsers.Datetime.Parse,
        help=(
            'Restores only the objects that were soft-deleted after this time.'
        ),
    )
    bulk_restore_flag_group.add_argument(
        '--deleted-before-time',
        type=arg_parsers.Datetime.Parse,
        help=(
            'Restores only the objects that were soft-deleted before this time.'
        ),
    )

  def Run(self, args):
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    self.exit_code = task_executor.execute_tasks(
        task_iterator=_restore_task_iterator(args),
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER, manifest_path=None
        ),
    )
