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
"""Implementation of rsync command for Cloud Storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Rsync(base.Command):
  """Synchronize content of two buckets/directories."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* makes the contents under `DESTINATION` the same as the
      contents under `SOURCE`, by copying any missing files/objects (or
      those whose data has changed), and (if `--delete` is specified) deleting
      any extra files/objects. `SOURCE` must specify a directory, bucket, or
      bucket subdirectory. *{command}* does not copy empty directory trees,
      since storage providers use a [flat namespace](https://cloud.google.com/storage/docs/folders).

      Note, shells (like bash, zsh) sometimes attempt to expand wildcards in
      ways that can be surprising. Also, attempting to copy files whose names
      contain wildcard characters can result in problems.

      If synchronizing a large amount of data between clouds you might consider
      setting up a Google Compute Engine account and running *{command}* there.
      Since *{command}* cross-provider data transfers flow through the machine
      where *{command}* is running, doing this can make your transfer run
      significantly faster than on your local workstation.

      """,
      'EXAMPLES':
          """
      To sync the contents of the local directory ``data'' to the bucket
      gs://my-bucket/data:

        $ {command} data gs://my-bucket/data

      To recurse into directories use `--recursive`:

        $ {command} data gs://my-bucket/data --recursive

      To make the local directory ``my-data'' the same as the contents of
      gs://mybucket/data and delete objects in the local directory that are not
      in gs://mybucket/data:

        $ {command} gs://mybucket/data my-data --recursive --delete

      To make the contents of gs://mybucket2 the same as gs://mybucket1 and
      delete objects in gs://mybucket2 that are not in gs://mybucket1:

        $ {command} gs://mybucket1 gs://mybucket2 --recursive --delete

      To copy all objects from ``dir1'' into ``dir2'' and delete all objects in
      ``dir2'' which are not in ``dir1'':

        $ {command} dir1 dir2 --recursive --delete

      To mirror your content across cloud providers:

        $ {command} gs://my-gs-bucket s3://my-s3-bucket --recursive --delete

      To apply gzip compression to only uploaded image files in ``dir'':

        $ {command} dir gs://my-bucket/data --gzip-transfer=jpeg,jpg,gif,png

      To skip the file ``dir/data1/a.txt'':

        $ {command} dir gs://my-bucket --exclude "data./.*\\.txt$"

      To skip all .txt and .jpg files in ``dir'':

        $ {command} dir gs://my-bucket --exclude ".*\\.txt$|.*\\.jpg$"
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('source', help='The source path to sync.')
    parser.add_argument('destination', help='The destination path.')
    parser.add_argument(
        '-a',
        '--canned-acl',
        help=textwrap.dedent("""\
            Sets named [canned ACL](https://cloud.google.com/storage/docs/access-control/lists#predefined-acl)
            when uploaded objects created. Note that {command} will decide
            whether or not to perform a copy based only on object size and
            modification time, not current ACL state. Also see `--preserve-acls`
            below."""))
    parser.add_argument(
        '-c',
        '--checksum',
        action='store_true',
        help=textwrap.dedent("""\
            Causes the rsync command to compute and compare checksums (instead
            of comparing mtime) for files if the size of source and destination
            match. This option increases local disk I/O and run time if either
            SOURCE or DESTINATION are on the local file system."""))
    parser.add_argument(
        '-d',
        '--delete',
        action='store_true',
        help=textwrap.dedent("""\
            Delete extra files under DESTINATION not found under SOURCE.
            By default extra files are not deleted.

            Note: this option can delete data quickly if you specify the wrong
            source/destination combination."""))
    parser.add_argument(
        '-e',
        '--exclude-symlinks',
        action='store_true',
        help=textwrap.dedent("""\
            Ignore symbolic links. Note that *{command}* does not follow
            directory symlinks, regardless of whether `--exclude-symlinks` is
            specified."""))
    parser.add_argument(
        '-i',
        '--ignore-existing',
        action='store_true',
        help=textwrap.dedent("""\
            Ignore any files which exist on the destination."""))
    parser.add_argument(
        '-j',
        '--gzip-transfer',
        metavar='EXTENSION',
        type=arg_parsers.ArgList(),
        help=textwrap.dedent("""\
            Applies gzip transport encoding to any file upload whose extension
            matches the provided list. This is useful when uploading files with
            compressible content (such as .js, .css, or .html files) because it
            saves network bandwidth while also leaving the data uncompressed in
            DESTINATION.

            When you specify `--gzip-transfer`, files being uploaded are
            compressed in-memory and on-the-wire only. Both the local files and
            cloud objects remain uncompressed. The uploaded objects retain the
            Content-Type and name of the original files."""))
    parser.add_argument(
        '-J',
        '--gzip-transfer-all',
        action='store_true',
        help=textwrap.dedent("""\
            Applies gzip transport encoding to all file uploads. This option
            works like `--gzip-transfer` described above, but it applies to all
            uploaded files, regardless of extension.

            Caution: If you use this option and some of the source files don't
            compress well (e.g., that's often true of binary data), this option
            may result in longer uploads."""))
    parser.add_argument(
        '-n',
        '--dry-run',
        action='store_true',
        help=textwrap.dedent("""\
            Causes rsync to run in "dry run" mode, i.e., just outputting what
            would be copied or deleted without actually doing any
            copying/deleting."""))
    parser.add_argument(
        '-p',
        '--preserve-acls',
        action='store_true',
        help=textwrap.dedent("""\
            Causes ACLs to be preserved when objects are copied. Note that
            *{command}* will decide whether or not to perform a copy based only
            on object size and modification time, not current ACL state.

            If the source and destination differ in size or modification time
            and `--preserve-acls` is used, the file will be copied and ACL
            preserved. However, if the source and destination don't differ in
            size or checksum but have different ACLs, `--preserve-acls` will
            have no effect."""))
    parser.add_argument(
        '-P',
        '--preserve-posix',
        action='store_true',
        help=textwrap.dedent("""\
            Preserve POSIX attributes when objects are copied. With this feature
            enabled, *{command}* will copy fields provided by the Linux command
            `stat` into object metadata. These are the user ID of the owner, the
            group ID of the owning group, the mode (permissions) of the file,
            and the access/modification time of the file. For downloads, these
            attributes will only be set if the source objects were uploaded with
            this flag enabled.

            On Windows, this flag will only set and restore access time and
            modification time. This is because Windows doesn't have a notion of
            POSIX uid/gid/mode."""))
    parser.add_argument(
        '-r',
        '-R',
        '--recursive',
        action='store_true',
        help=textwrap.dedent("""\
            Synchronize directories, buckets, and bucket subdirectories
            recursively. If you neglect to use this option *{command}* will make
            only the top-level directory in SOURCE and DESTINATION match,
            skipping any sub-directories."""))
    parser.add_argument(
        '-u',
        '--update',
        action='store_true',
        help=textwrap.dedent("""\
            When a file/object is present in both the source and destination, if
            `mtime` is available for both, do not perform the copy if the
            destination `mtime` is newer."""))
    parser.add_argument(
        '-U',
        '--skip-unsupported',
        action='store_true',
        help=textwrap.dedent("""\
            Skip objects with unsupported object types instead of failing.
            Unsupported object types are Amazon S3 Objects in the `GLACIER`
            storage class."""))
    parser.add_argument(
        '-x',
        '--exclude',
        metavar='REGEX',
        help=textwrap.dedent("""\
            Exclude files/objects matching pattern, i.e., any matching
            files/objects are not copied or deleted.

            Note that the pattern is a Python regular expression, not a wildcard
            (so, matching any string ending in "abc" would be specified using
            ``.*abc$'' rather than ``*abc''). Note also that the exclude path is
            always relative (similar to Linux `rsync` or `tar` exclude options).

            When using the Windows cmd.exe command line interpreter, use
            ``^'' as an escape character instead of ``\'' and escape the ``|''
            character. When using Windows PowerShell, use ``''' instead of ``"''
            and surround the ``|'' character with ``"''."""))

  def Run(self, args):
    raise NotImplementedError
