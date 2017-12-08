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
"""Commands for updating backend buckets."""

import copy

from googlecloudsdk.api_lib.compute import backend_buckets_utils
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.backend_buckets import flags as backend_buckets_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base_classes.ReadWriteCommand):
  """Update a backend bucket."""

  @staticmethod
  def Args(parser):
    backend_buckets_utils.AddUpdatableArgs(parser)
    backend_buckets_flags.GCS_BUCKET_ARG.AddArgument(parser)

  @property
  def service(self):
    return self.compute.backendBuckets

  @property
  def resource_type(self):
    return 'backendBuckets'

  def CreateReference(self, args):
    return backend_buckets_flags.BACKEND_BUCKET_ARG.ResolveAsResource(
        args, self.resources)

  def GetGetRequest(self, args):
    return (
        self.service,
        'Get',
        self.messages.ComputeBackendBucketsGetRequest(
            project=self.project,
            backendBucket=self.ref.Name()))

  def GetSetRequest(self, args, replacement, _):
    return (
        self.service,
        'Update',
        self.messages.ComputeBackendBucketsUpdateRequest(
            project=self.project,
            backendBucket=self.ref.Name(),
            backendBucketResource=replacement))

  def Modify(self, args, existing):
    replacement = copy.deepcopy(existing)

    if args.description:
      replacement.description = args.description
    elif args.description == '':  # pylint: disable=g-explicit-bool-comparison
      replacement.description = None

    if args.gcs_bucket_name:
      replacement.bucketName = args.gcs_bucket_name

    if args.enable_cdn is not None:
      replacement.enableCdn = args.enable_cdn

    return replacement

  def Run(self, args):
    if not any([
        args.description is not None,
        args.gcs_bucket_name is not None,
        args.enable_cdn is not None,
    ]):
      raise exceptions.ToolException('At least one property must be modified.')

    return super(Update, self).Run(args)


Update.detailed_help = {
    'brief': 'Update a backend bucket',
    'DESCRIPTION': """
        *{command}* is used to update backend buckets.
        """,
}
