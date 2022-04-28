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

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.cp import copy_task_iterator
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


_ALL_VERSIONS_HELP_TEXT = """\
Copy all source versions from a source bucket or folder. If not set, only the
live version of each source object is copied.

Note: This option is only useful when the destination bucket has Object
Versioning enabled. Additionally, the generation numbers of copied versions do
not necessarily match the order of the original generation numbers.
"""
# TODO(b/223800321): Maybe offer ability to limit parallel encoding workers.
_GZIP_IN_FLIGHT_EXTENSIONS_HELP_TEXT = """\
Applies gzip transport encoding to any file upload whose
extension matches the input extension list. This is useful when
uploading files with compressible content such as .js, .css,
or .html files. This also saves network bandwidth while
leaving the data uncompressed in Cloud Storage.

When you specify the `--gzip-in-flight` option, files being uploaded are
compressed in-memory and on-the-wire only. Both the local
files and Cloud Storage objects remain uncompressed. The
uploaded objects retain the `Content-Type` and name of the
original files."""
_GZIP_IN_FLIGHT_ALL_HELP_TEXT = """\
Applies gzip transport encoding to file uploads. This option
works like the `--gzip-transfer` option described above, but it
applies to all uploaded files, regardless of extension.

CAUTION: If some of the source files don't compress well, such
as binary data, using this option may result in longer uploads."""
_MANIFEST_HELP_TEXT = """\
Outputs a manifest log file with detailed information about each item that
was copied. This manifest contains the following information for each item:

- Source path.
- Destination path.
- Source size.
- Bytes transferred.
- MD5 hash.
- Transfer start time and date in UTC and ISO 8601 format.
- Transfer completion time and date in UTC and ISO 8601 format.
- Final result of the attempted transfer: OK, error, or skipped.
- Details, if any.

If the manifest file already exists, gcloud storage appends log items to the
existing file.

Objects that are marked as "OK" or "skipped" in the existing manifest file
are not retried by future commands. Objects marked as "error" are retried.
"""


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

      Use the `--recursive` option to copy an entire directory tree. The
      following command uploads the directory tree ``dir'':

        $ {command} --recursive dir gs://my-bucket
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('source', nargs='+', help='The source path(s) to copy.')
    parser.add_argument('destination', help='The destination path.')
    parser.add_argument(
        '-A',
        '--all-versions',
        action='store_true',
        help=_ALL_VERSIONS_HELP_TEXT)
    parser.add_argument(
        '-R',
        '-r',
        '--recursive',
        action='store_true',
        help='Recursively copy the contents of any directories that match the'
        ' source path expression.')
    parser.add_argument(
        '--do-not-decompress',
        action='store_true',
        help='Do not automatically decompress downloaded gzip files.')
    parser.add_argument(
        '--ignore-symlinks',
        action='store_true',
        help='Ignore file symlinks instead of copying what they point to.'
        ' Symlinks pointing to directories will always be ignored.')
    parser.add_argument('-L', '--manifest-path', help=_MANIFEST_HELP_TEXT)
    parser.add_argument(
        '-n',
        '--no-clobber',
        action='store_true',
        help='Do not overwrite existing files or objects at the destination.'
        ' Skipped items will be printed. This option performs an additional GET'
        ' request for cloud objects before attempting an upload.')
    parser.add_argument(
        '-v',
        '--print-created-message',
        action='store_true',
        help='Prints the version-specific URL for each copied object.')
    parser.add_argument(
        '-U',
        '--skip-unsupported',
        action='store_true',
        help='Skip objects with unsupported object types.'
        'Currently, the only unsupported category is Amazon S3 objects with the'
        ' GLACIER storage class.')
    parser.add_argument(
        '-s',
        '--storage-class',
        help='Specify the storage class of the destination object. If not'
        ' specified, the default storage class of the destination bucket is'
        ' used. This option is not valid for copying to non-cloud destinations.'
    )
    gzip_flags_group = parser.add_group(mutex=True)
    gzip_flags_group.add_argument(
        '-J',
        '--gzip-in-flight-all',
        action='store_true',
        help=_GZIP_IN_FLIGHT_ALL_HELP_TEXT)
    gzip_flags_group.add_argument(
        '-j',
        '--gzip-in-flight-extensions',
        metavar='FILE_EXTENSIONS',
        type=arg_parsers.ArgList(),
        help=_GZIP_IN_FLIGHT_EXTENSIONS_HELP_TEXT)
    flags.add_continue_on_error_flag(parser)
    flags.add_precondition_flags(parser)
    flags.add_object_metadata_flags(parser)
    flags.add_encryption_flags(parser)

  def Run(self, args):
    if args.no_clobber and args.if_generation_match:
      raise ValueError(
          'Cannot specify both generation precondition and no-clobber.')

    encryption_util.initialize_key_store(args)

    source_expansion_iterator = name_expansion.NameExpansionIterator(
        args.source,
        all_versions=args.all_versions,
        recursion_requested=args.recursive,
        ignore_symlinks=args.ignore_symlinks)
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()

    raw_destination_url = storage_url.storage_url_from_string(args.destination)
    if (isinstance(raw_destination_url, storage_url.FileUrl) and
        args.storage_class):
      raise ValueError(
          'Cannot specify storage class for a non-cloud destination: {}'.format(
              raw_destination_url))

    parallelizable = True
    shared_stream = None
    if (args.all_versions and
        (properties.VALUES.storage.process_count.GetInt() != 1 or
         properties.VALUES.storage.thread_count.GetInt() != 1)):
      log.warning(
          'Using sequential instead of parallel task execution. This will'
          ' maintain version ordering when copying all versions of an object.')
      parallelizable = False
    if (isinstance(raw_destination_url, storage_url.FileUrl) and
        raw_destination_url.is_pipe):
      log.warning('Downloading to a pipe.'
                  ' This command may stall until the pipe is read.')
      parallelizable = False
      shared_stream = files.BinaryFileWriter(args.destination)

    user_request_args = (
        user_request_args_factory.get_user_request_args_from_command_args(
            args, metadata_type=user_request_args_factory.MetadataType.OBJECT))
    task_iterator = copy_task_iterator.CopyTaskIterator(
        source_expansion_iterator,
        args.destination,
        custom_md5_digest=args.content_md5,
        do_not_decompress=args.do_not_decompress,
        print_created_message=args.print_created_message,
        shared_stream=shared_stream,
        skip_unsupported=args.skip_unsupported,
        task_status_queue=task_status_queue,
        user_request_args=user_request_args,
    )
    self.exit_code = task_executor.execute_tasks(
        task_iterator,
        parallelizable=parallelizable,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            task_status.IncrementType.FILES_AND_BYTES,
            manifest_path=user_request_args.manifest_path,
        ),
        continue_on_error=args.continue_on_error,
    )

    if shared_stream:
      shared_stream.close()
