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
from googlecloudsdk.command_lib.storage import errors
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
  requires_rewrite = (
      args.encryption_key or args.clear_encryption_key or args.storage_class)
  if requires_rewrite:
    task_type = rewrite_object_task.RewriteObjectTask
  else:
    task_type = patch_object_task.PatchObjectTask

  user_request_args = (
      user_request_args_factory.get_user_request_args_from_command_args(
          args, metadata_type=user_request_args_factory.MetadataType.OBJECT))
  if (requires_rewrite or
      user_request_args_factory.modifies_full_acl_policy(user_request_args)):
    # TODO(b/244621490): Add test when ACL flags are exposed.
    fields_scope = cloud_api.FieldsScope.FULL
  else:
    fields_scope = cloud_api.FieldsScope.SHORT

  urls = stdin_iterator.get_urls_iterable(args.url, args.read_paths_from_stdin)
  for url_string in urls:
    url = storage_url.storage_url_from_string(url_string)
    if args.recursive:
      potentially_recursive_url = url.join('**')
    else:
      potentially_recursive_url = url
    errors.raise_error_if_not_cloud_object(args.command_path,
                                           potentially_recursive_url)
    for object_resource in wildcard_iterator.get_wildcard_iterator(
        potentially_recursive_url.url_string, fields_scope=fields_scope):
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
  flags.add_object_acl_setter_flags(parser)
  flags.add_object_metadata_flags(parser, allow_patch=True)


def _add_alpha_args(parser):
  """Register flags for the alpha version of this command.

  Args:
    parser (argparse.ArgumentParser): The parser to add the arguments to.

  Returns:
    objects update flag group
  """
  parser.add_argument(
      '--add-acl-grant',
      hidden=True,
      help='JSON object in the format accepted by your cloud provider.'
      ' For example, for GCS, `--add-acl-grant=entity=user-tim@gmail.com,'
      'role=OWNER`')
  parser.add_argument(
      '--event-based-hold',
      action=arg_parsers.StoreTrueFalseAction,
      help='Enables or disables an event-based hold on objects.')
  parser.add_argument(
      '--remove-acl-grant',
      hidden=True,
      help='JSON object in the format accepted by your cloud provider.'
      ' For example, for GCS, `--remove-acl-grant=ENTITY`, where `ENTITY`'
      ' has a valid ACL entity format, such as `user-tim@gmail.com`,'
      ' `group-admins`, `allUsers`, etc.')
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
    if not args.predefined_acl and args.preserve_acl is None:
      # Preserve ACLs by default if nothing set by user.
      args.preserve_acl = True
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
