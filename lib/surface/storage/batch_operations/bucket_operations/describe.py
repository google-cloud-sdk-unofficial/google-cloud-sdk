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
"""Implementation of describe command for batch job bucket operations."""

from googlecloudsdk.api_lib.storage import storage_batch_operations_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.batch_operations.jobs import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Describe a bucket operation for a batch operation job."""

  detailed_help = {
      'DESCRIPTION': """
      Describe a single bucket operation for a batch operation job.
      """,
      'EXAMPLES': """
      The following example command describes bucket operation `bo-1` for batch job `my-job`:

          $ {command} bo-1 --job=my-job

      The following example command describes bucket operation `bo-1` using its fully qualified name:

          $ {command} projects/my-project/locations/global/jobs/my-job/bucketOperations/bo-1
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.add_bucket_operation_resource_arg(parser, 'describe')

  def Run(self, args):
    bucket_op_ref = args.CONCEPTS.bucket_operation.Parse()
    return storage_batch_operations_api.StorageBatchOperationsApi().get_bucket_operation(
        bucket_operation_name=bucket_op_ref.RelativeName(),
    )
