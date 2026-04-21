# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Command for deleting backend buckets."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.backend_buckets import flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.PREVIEW)
@base.UniverseCompatible
class Delete(base.DeleteCommand):
  """Delete backend buckets.

  *{command}* deletes one or more backend buckets.
  """

  BACKEND_BUCKET_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.BACKEND_BUCKET_ARG = flags.GLOBAL_REGIONAL_MULTI_BACKEND_BUCKET_ARG
    cls.BACKEND_BUCKET_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.BackendBucketsCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    backend_bucket_refs = self.BACKEND_BUCKET_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
        default_scope=compute_scope.ScopeEnum.GLOBAL,
    )

    utils.PromptForDeletion(backend_bucket_refs)

    requests = []
    for backend_bucket_ref in backend_bucket_refs:
      if backend_bucket_ref.Collection() == 'compute.regionBackendBuckets':
        requests.append((
            client.apitools_client.regionBackendBuckets,
            'Delete',
            client.messages.ComputeRegionBackendBucketsDeleteRequest(
                **backend_bucket_ref.AsDict()
            ),
        ))
      else:
        requests.append((
            client.apitools_client.backendBuckets,
            'Delete',
            client.messages.ComputeBackendBucketsDeleteRequest(
                **backend_bucket_ref.AsDict()
            ),
        ))

    return client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class DeleteBeta(Delete):
  """Delete backend buckets.

  *{command}* deletes one or more backend buckets.

  To delete a global backend bucket, run either of the following:

      $ {command} my-backend-bucket
        --gcs-bucket-name gcs-bucket-1
        --global

      $ {command} my-backend-bucket
        --gcs-bucket-name gcs-bucket-1

  To delete a regional backend bucket, run the following:

      $ {command} my-backend-bucket
        --gcs-bucket-name gcs-bucket-1
        --region=us-central1
  """

  pass


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class DeleteAlpha(DeleteBeta):
  """Delete backend buckets.

  *{command}* deletes one or more backend buckets.

  To delete a global backend bucket, run either of the following:

      $ {command} my-backend-bucket
        --gcs-bucket-name gcs-bucket-1
        --global

      $ {command} my-backend-bucket
        --gcs-bucket-name gcs-bucket-1

  To delete a regional backend bucket, run the following:

      $ {command} my-backend-bucket
        --gcs-bucket-name gcs-bucket-1
        --region=us-central1
  """

  pass
