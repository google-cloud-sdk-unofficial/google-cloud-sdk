# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Implementation of list command for batch job bucket operations."""

from googlecloudsdk.api_lib.storage import storage_batch_operations_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.batch_operations.jobs import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  """List bucket operations for a batch operation job."""

  detailed_help = {
      'DESCRIPTION': """
      List bucket operations for a specific batch operation job.
      """,
      'EXAMPLES': """
      The following example command lists bucket operations for batch job `my-job`:

          $ {command} --job=my-job

      The following example command lists bucket operations for batch job `my-job`
      filtering by bucket name `my-bucket`:

          $ {command} --job=my-job --buckets=my-bucket
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_batch_job_flag_resource_arg(
        parser, 'for which to list bucket operations'
    )
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--buckets',
        type=arg_parsers.ArgList(),
        metavar='BUCKETS',
        help='If provided, only show operations for buckets in the list.',
    )
    parser.display_info.AddFormat("""
      table(
        name.basename():label=BUCKET_OPERATION_ID,
        bucketName:label=BUCKET,
        counters:wrap=20:label=COUNTERS,
        errorSummaries:wrap=20:label=ERROR_SUMMARIES,
        state:wrap=20:label=STATE,
        createTime.date():label=CREATE_TIME,
        completeTime.date():label=COMPLETION_TIME
      )
    """)

  def Run(self, args):
    job_ref = args.CONCEPTS.job.Parse()
    return storage_batch_operations_api.StorageBatchOperationsApi().list_bucket_operations(
        batch_job_name=job_ref.RelativeName(),
        bucket_names=args.buckets,
        page_size=args.page_size,
    )
