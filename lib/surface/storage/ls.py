# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""Command to list Cloud Storage objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks.ls import cloud_list_task


class Ls(base.Command):
  """List the objects in Cloud Storage buckets."""

  # pylint:disable=g-backslash-continuation
  detailed_help = {
      'DESCRIPTION': """\
      *{command}* lets you list the objects in your Cloud Storage buckets.
      Forward slashes in object names are logically treated as directories for
      the purposes of listing contents. See below for example of how to use
      wildcards to get the listing behavior you want.
      """,
      'EXAMPLES': """\
      To list the buckets in current project:

      $ gcloud alpha storage ls

      To list the contents of a bucket:

          $ {command} gs://my-bucket

      You can use wildcards to match multiple paths (including multiple
      buckets). Bucket wildcards are expanded only to the buckets contained in
      your current project:

          $ {command} gs://my-b*/log*.txt

      The following wildcards are valid and match only within the current
      directory:

          *: Matches zero or more characters
          ?: Matches zero or one characters
          []: Matches a character range (ex. [a-z] or [0-9])

      You can use double-star wildcards to match zero or more directory levels
      in a path:

          $ {command} gs://my-bucket/**/log*.txt

      You can also use double-star to match all files after a root in a path:

          $ {command} gs://my-bucket/**

      Double-star expansion can not be combined with other expressions in a
      given path segment and will operate as a single star in that context. For
      example:

          gs://my-bucket/dir**/log.txt      is treated as:

          gs://my-bucket/dir*/log.txt       and instead should be written as:

          gs://my-bucket/dir*/**/log.txt    to get the recursive behavior.

      List all items recursively with formatting by using -r:

      $ {command} ls -r gs://bucket

      Recursive listings are similar to ** except with line breaks and header
      formatting for each container.
      """
  }
  # pylint:enable=g-backslash-continuation

  @staticmethod
  def Args(parser):
    """Edit argparse.ArgumentParser for the command."""
    parser.add_argument(
        'path',
        nargs='*',
        help='The path of objects and directories to list. The path must begin'
             ' with gs:// and may or may not contain wildcard characters.')
    parser.add_argument(
        '-R', '-r', '--recursive',
        action='store_true',
        help='Recursively list the contents of any directories that match the'
             ' path expression.')

  def Run(self, args):
    """Command execution logic."""
    if args.path:
      storage_urls = [storage_url.storage_url_from_string(path)
                      for path in args.path]
      for url in storage_urls:
        if not isinstance(url, storage_url.CloudUrl):
          raise errors.InvalidUrlError('Ls only works for cloud URLs.'
                                       ' Error for: {}'.format(url.url_string))
    else:
      storage_urls = [storage_url.CloudUrl(cloud_api.DEFAULT_PROVIDER)]

    tasks = [
        cloud_list_task.CloudListTask(
            url, recursion_flag=args.recursive) for url in storage_urls]
    task_executor.ExecuteTasks(tasks)
