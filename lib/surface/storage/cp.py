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
"""Implementation of Unix-like cp command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import multiprocessing

from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.cp import copy_task_iterator


class Cp(base.Command):
  """Upload, download, and copy Cloud Storage objects."""

  detailed_help = {
      'DESCRIPTION':
          """
      Copy data between your local file system and the cloud, within the cloud,
      and between cloud storage providers.
      """,
      'EXAMPLES':
          """

      The following command uploads all text files from the local directory to a
      bucket:

        $ {command} *.txt gs://my-bucket

      The following command downloads all text files from a bucket to your
      current directory:

        $ {command} gs://my-bucket/*.txt .

      The following command transfers all text files from a bucket to a
      different cloud storage provider:

        $ {command} gs://my-bucket/*.txt s3://my-bucket

      Use the -r option to copy an entire directory tree. The following command
      uploads the directory tree "dir":

        $ {command} -r dir gs://my-bucket
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('source', nargs='+', help='The source path(s) to copy.')
    parser.add_argument('destination', help='The destination path.')
    parser.add_argument(
        '-R',
        '-r',
        '--recursive',
        action='store_true',
        help='Recursively copy the contents of any directories that match the'
        ' source path expression.')
    flags.add_precondition_flags(parser)
    flags.add_object_metadata_flags(parser)

  def Run(self, args):
    source_expansion_iterator = name_expansion.NameExpansionIterator(
        args.source, recursion_requested=args.recursive)
    task_status_queue = multiprocessing.Queue()
    user_request_args = request_config_factory.get_user_request_args_from_command_args(
        args)
    task_iterator = copy_task_iterator.CopyTaskIterator(
        source_expansion_iterator,
        args.destination,
        custom_md5_digest=args.content_md5,
        task_status_queue=task_status_queue,
        user_request_args=user_request_args,
    )
    self.exit_code = task_executor.execute_tasks(
        task_iterator,
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_type=task_status.ProgressType.FILES_AND_BYTES,
    )
