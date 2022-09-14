# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of objects update command for updating object settings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import stdin_iterator
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.objects import patch_object_task
from googlecloudsdk.command_lib.storage.tasks.objects import rewrite_object_task


def _get_task_iterator(args):
  """Yields PatchObjectTask's or RewriteObjectTask's."""
  if args.encryption_key or args.clear_encryption_key or args.storage_class:
    fields_scope = cloud_api.FieldsScope.FULL
    task_type = rewrite_object_task.RewriteObjectTask
  else:
    fields_scope = cloud_api.FieldsScope.SHORT
    task_type = patch_object_task.PatchObjectTask

  user_request_args = (
      user_request_args_factory.get_user_request_args_from_command_args(
          args, metadata_type=user_request_args_factory.MetadataType.OBJECT))
  urls = stdin_iterator.get_urls_iterable(args.url, args.read_paths_from_stdin)
  for url in urls:
    if args.recursive:
      potentially_recursive_url = storage_url.storage_url_from_string(url).join(
          '**').url_string
    else:
      potentially_recursive_url = url
    for object_resource in wildcard_iterator.get_wildcard_iterator(
        potentially_recursive_url, fields_scope=fields_scope):
      yield task_type(object_resource, user_request_args=user_request_args)


def _add_common_args(parser):
  """Register flags for this command.

  Args:
    parser (argparse.ArgumentParser): The parser to add the arguments to.

  Returns:
    objects update flag group
  """
  parser.add_argument(
      'url', nargs='*', help='Specifies URLs of objects to update.')
  parser.add_argument(
      '-p',
      '--preserve-acl',
      action='store_true',
      default=True,
      help='Preserves ACLs when copying in the cloud. This feature is'
      ' supported for only Google Cloud Storage and requires OWNER access'
      " to all copied objects. To use the destination bucket's default policy"
      ' (necessary for uniform bucket-level access), use --no-preserve-acl.')
  parser.add_argument(
      '--read-paths-from-stdin',
      '-I',
      action='store_true',
      help='Read the list of objects to update from stdin. No need to enter'
      ' a source argument if this flag is present.\nExample:'
      ' "storage objects update -I --content-type=new-type"')
  parser.add_argument(
      '-R',
      '-r',
      '--recursive',
      action='store_true',
      help='Recursively update objects under any buckets or directories that'
      ' match the URL expression.')
  parser.add_argument(
      '-s',
      '--storage-class',
      help='Specify the storage class of the object. Using this flag triggers'
      ' a rewrite of underlying object data.')

  flags.add_continue_on_error_flag(parser)
  flags.add_encryption_flags(parser, allow_patch=True)
  flags.add_precondition_flags(parser)
  flags.add_object_metadata_flags(parser, allow_patch=True)


def _add_alpha_args(parser):
  """Register flags for the alpha version of this command.

  Args:
    parser (argparse.ArgumentParser): The parser to add the arguments to.

  Returns:
    objects update flag group
  """
  parser.add_argument(
      '--event-based-hold',
      action=arg_parsers.StoreTrueFalseAction,
      help='Enables or disables an event-based hold on objects.')
  parser.add_argument(
      '--temporary-hold',
      action=arg_parsers.StoreTrueFalseAction,
      help='Enables or disables a temporary hold on objects.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update Cloud Storage objects."""

  detailed_help = {
      'DESCRIPTION':
          """
      Update Cloud Storage objects.
      """,
      'EXAMPLES':
          """

      Update a Google Cloud Storage object's custom-metadata:

        $ {command} gs://bucket/my-object --custom-metadata=key1=value1,key2=value2

      Rewrite all JPEG images to the NEARLINE storage class:

        $ {command} gs://bucket/*.jpg --storage-class=NEARLINE

       You can also provide a precondition on an object's metageneration in
       order to avoid potential race conditions:

        $ {command} gs://bucket/*.jpg --storage-class=NEARLINE --if-metageneration-match=123456789
      """,
  }

  @staticmethod
  def Args(parser):
    _add_common_args(parser)

  def Run(self, args):
    encryption_util.initialize_key_store(args)
    task_iterator = _get_task_iterator(args)

    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    self.exit_code = task_executor.execute_tasks(
        task_iterator,
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER,
            manifest_path=None),
        continue_on_error=args.continue_on_error,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update Cloud Storage objects."""

  @staticmethod
  def Args(parser):
    _add_common_args(parser)
    _add_alpha_args(parser)
