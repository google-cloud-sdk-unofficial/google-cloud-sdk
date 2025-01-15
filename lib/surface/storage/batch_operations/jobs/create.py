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
"""Implementation of create command for batch actions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import storage_batch_operations_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage.batch_operations.jobs import resource_args
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Create a new batch operation job."""

  detailed_help = {
      "DESCRIPTION": """
      Create a batch operation job, allowing you to perform operations
      such as deletion, updating metadata, and more on objects in a
      serverless manner.
      """,
      "EXAMPLES": """
      To create a batch job with the name `my-job` to perform object deletion
      where the manifest file
      `gs://my-bucket/manifest.csv` specifies the objects to be transformed:

          $ {command} my-job --manifest-location=gs://my-bucket/manifest.csv
          --delete-object

      To create a batch job with the name `my-job` to update object metadata
      `Content-Disposition` to `inline` and `Content-Language` to `en` where
      the prefix list file
      `my-path/my-prefix-list.json` specifies the objects to be transformed:

          $ {command} my-job --prefix-list-file=my-path/my-prefix-list.json
          --put-metadata=Content-Disposition=inline,Content-Language=en
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_batch_job_resource_arg(parser, "to create")
    flags.add_batch_jobs_flags(parser)

  def Run(self, args):
    job_ref = args.CONCEPTS.batch_job.Parse()
    storage_batch_operations_api.StorageBatchOperationsApi().create_batch_job(
        args, job_ref.RelativeName()
    )
    log.status.Print("Created batch job: {}".format(job_ref.RelativeName()))
