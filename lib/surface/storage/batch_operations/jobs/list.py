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
"""Implementation of list command for batch operations jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import storage_batch_operations_api
from googlecloudsdk.calliope import base


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List batch-operations jobs."""

  detailed_help = {
      "DESCRIPTION": """
      List batch operation jobs.
      """,
      "EXAMPLES": """
      To list all batch jobs in all locations:

          $ {command}

      To list all batch jobs for location `us-central1`:

          $ {command} --location=us-central1

      To list all batch jobs for location `us-central1` with a page size of `10`:

          $ {command} --location=us-central1 --page-size=10

      To list a limit of `20` batch jobs for location `us-central1`:

          $ {command} --location=us-central1 --limit=20

      To list all batch jobs for location `us-central1` in `JSON` format:

          $ {command} --location=us-central1 --format=json
      """,
  }

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        "--location",
        type=str,
        help="The location of the batch jobs.",
    )
    parser.display_info.AddFormat("""
      table(
        name.basename():wrap=20:label=BATCH_JOB_ID,
        firstof(prefixList, manifest):wrap=20:label=SOURCE,
        firstof(putObjectHold, deleteObject, putKmsKey, putMetadata):wrap=20:label=TRANSFORMATION,
        createTime:wrap=20:label=CREATE_TIME,
        counters:wrap=20:label=COUNTERS,
        errorSummaries:wrap=20:label=ERROR_SUMMARIES,
        state:wrap=20:label=STATE
      )
    """)

  def Run(self, args):
    return storage_batch_operations_api.StorageBatchOperationsApi().list_batch_jobs(
        args.location, args.limit, args.page_size
    )
