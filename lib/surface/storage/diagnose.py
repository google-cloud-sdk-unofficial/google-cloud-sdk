# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Diagnose Google Cloud Storage common issues."""

import enum
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.diagnose import download_throughput_diagnostic
from googlecloudsdk.command_lib.storage.diagnose import upload_throughput_diagnostic


class PerformanceTestType(enum.Enum):
  """Enum class for specifying performance test type for diagnostic tests."""

  DOWNLOAD_THROUGHPUT = 'DOWNLOAD_THROUGHPUT'
  UPLOAD_THROUGHPUT = 'UPLOAD_THROUGHPUT'
  LATENCY = 'LATENCY'


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Diagnose(base.Command):
  """Diagnose Google Cloud Storage."""

  detailed_help = {
      'DESCRIPTION': """
      The diagnose command runs a series of diagnostic tests for common gcloud
      storage issues.

      The `URL` argument must name an exisiting bucket for which the user
      already has write permissions. Standard billing also applies.
      Several test files/objects will be uploaded and downloaded to this bucket
      to gauge out the performance metrics. All the temporary files will be
      deleted on successfull completion of the command.

      By default, the command executes `DOWNLOAD_THROUGHPUT`,
      `UPLOAD_THROUGHPUT` and `LATENCY` tests. Tests to execute can be overriden
      by using the `--test-type` flag.
      Each test uses the command defaults or gcloud CLI configurations for
      performing the operations. This command also provides a way to override
      these values via means of different flags like `--process-count`,
      `--thread-count`, `--download-type`, etc.

      The command outputs a diagnostic report with sytem information like free
      memory, available CPU, average CPU load per test, disk counter deltas and
      diagnostic information specific to individual tests on successful
      completion.

      """,
      'EXAMPLES': """

      The following command runs the default diagnostic tests on ``my-bucket''
      bucket:

      $ {command} gs://my-bucket

      The following command runs only UPLOAD_THROUGHPUT and DOWNLOAD_THROUGHPUT
      diagnostic tests:

      $ {command} gs://my-bucket --test-type=[UPLOAD_THROUGHPUT,DOWNLOAD_THROUGHPUT]

      The following command runs the diagnostic tests using ``10'' objects of
      ``1MiB'' size each with ``10'' threads and ``10'' processes at max:

      $ {command} gs://my-bucket --no-of-objects=10 --object-size=1MiB
      --process-count=10 --thread-count=10

      The following command can be used to bundle and export the diagnostic
      information to a user defined ``PATH'' destination:

      $ {command} gs://my-bucket --export --destination=<PATH>
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.SetSortArgs(False)

    parser.add_argument(
        'url',
        type=str,
        nargs=1,
        help='Bucket URL to use for the diagnostic tests.',
    )
    parser.add_argument(
        '--test-type',
        type=arg_parsers.ArgList(
            choices=sorted([option.value for option in PerformanceTestType])
        ),
        metavar='TEST_TYPES',
        help="""
        Tests to run as part of this diagnosis. Following tests are supported:

        DOWNLOAD_THROUGHPUT: Upload objects to the specified bucket and record
        the number of bytes transfered per second.

        UPLOAD_THROUGHPUT: Download objects from the specified bucket and record
        the number of bytes transfered per second.

        LATENCY: Writes the objects, retrieves its metadata, reads the objects
        and records latency of each operation.
        """,
        default=[],
    )
    parser.add_argument(
        '--download-type',
        choices=sorted([
            option.value
            for option in download_throughput_diagnostic.DownloadType
        ]),
        help="""
        Download strategy to use for the DOWNLOAD_THROUGHPUT diagnostic test.

        STREAMING: Downloads the file in memory, does not use parallelism.
        `--process-count` and `--thread-count` flag values will be ignored if
        provided.

        SLICED: Performs a [sliced download](https://cloud.google.com/storage/docs/sliced-object-downloads)
        of objects to a directory.
        Parallelism can be controlled via `--process-count` and `--thread-count`
        flags.

        FILE: Download objects as files. Parallelism can be controlled via
        `--process-count` and `--thread-count` flags.
        """,
    )
    parser.add_argument(
        '--upload-type',
        choices=sorted(
            [option.value for option in upload_throughput_diagnostic.UploadType]
        ),
        help="""
        Upload strategy to use for the _UPLOAD_THROUGHPUT_ diagnostic test.

        FILE: Uploads files to a bucket. Parallelism can be controlled via
        `--process-count` and `--thread-count` flags.

        PARALLEL_COMPOSITE: Uploads files using a [parallel
        composite strategy](https://cloud.google.com/storage/docs/parallel-composite-uploads).
        Parallelism can be controlled via `--process-count` and `--thread-count`
        flags.

        STREAMING: Streams the data to the bucket, does not use parallelism.
        `--process-count` and `--thread-count` flag values will be ignored if
        provided.
        """,
    )
    parser.add_argument(
        '--object-count',
        type=int,
        help='Number of objects to use for each diagnostic test.',
    )
    parser.add_argument(
        '--process-count',
        type=int,
        help='Number of processes at max to use for each diagnostic test.',
    )
    parser.add_argument(
        '--thread-count',
        type=int,
        help='Number of threads at max to use for each diagnostic test.',
    )

    object_properties_group = parser.add_group(
        mutex=True, sort_args=False, help='Object properties:'
    )
    object_properties_group.add_argument(
        '--object-size',
        type=arg_parsers.BinarySize(),
        help='Object size to use for the diagnostic tests.',
    )
    object_properties_group.add_argument(
        '--object-sizes',
        metavar='OBJECT_SIZES',
        type=arg_parsers.ArgList(element_type=arg_parsers.BinarySize()),
        help="""
        List of object sizes to use for the tests. Sizes should be
        provided for each object specified using `--no-of-objects` flag.
        """,
    )

    export_group = parser.add_group(
        sort_args=False, help='Export diagnostic bundle.'
    )
    export_group.add_argument(
        '--export',
        type=arg_parsers.ArgBoolean(),
        required=True,
        help="""
        Generate and export a diagnostic bundle. The following
        information will be bundled and exported into a gzipped tarball
        (.tar.gz):

        - Latest gcloud CLI logs.
        - Output of running the `gcloud storage diagnose` command.
        - Output of running the `gcloud info --anonymize` command.

        Note: This command generates a bundle containing system information like
        disk counter detlas, CPU information and system configurations. Please
        exercise caution while sharing.
        """,
    )
    export_group.add_argument(
        '--destination',
        type=str,
        help=(
            'Destination file path where the diagnostic bundle will be'
            ' exported.'
        ),
    )

  def Run(self, args):
    # TODO(b/330131442) : Implement the commnd.
    raise NotImplementedError
