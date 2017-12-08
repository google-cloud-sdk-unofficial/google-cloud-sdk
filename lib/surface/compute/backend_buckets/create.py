# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for creating backend buckets."""

from googlecloudsdk.api_lib.compute import backend_buckets_utils
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.backend_buckets import flags as backend_buckets_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base_classes.BaseAsyncCreator):
  """Create a backend bucket."""

  @staticmethod
  def Args(parser):
    backend_buckets_utils.AddUpdatableArgs(parser)
    backend_buckets_flags.REQUIRED_GCS_BUCKET_ARG.AddArgument(parser)

  @property
  def service(self):
    return self.compute.backendBuckets

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'backendBuckets'

  def CreateRequests(self, args):
    backend_buckets_ref = (
        backend_buckets_flags.BACKEND_BUCKET_ARG.ResolveAsResource(
            args, self.resources,
            default_scope=flags.ScopeEnum.GLOBAL))
    request = self.messages.ComputeBackendBucketsInsertRequest(
        backendBucket=self.messages.BackendBucket(
            description=args.description,
            name=backend_buckets_ref.Name(),
            bucketName=args.gcs_bucket_name),
        project=self.project)

    return [request]

CreateAlpha.detailed_help = {
    'brief': 'Create a backend bucket',
    'DESCRIPTION': """
        *{command}* is used to create backend buckets. Backend buckets
        define a Google Cloud Storage bucket that can serve content. URL
        maps define which requests are sent to which backend buckets.
    """,
}
