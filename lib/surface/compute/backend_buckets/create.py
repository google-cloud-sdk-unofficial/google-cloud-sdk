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
"""Command for creating backend buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import cdn_flags_utils as cdn_flags
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute import signed_url_flags
from googlecloudsdk.command_lib.compute.backend_buckets import backend_buckets_utils
from googlecloudsdk.command_lib.compute.backend_buckets import flags as backend_buckets_flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class Create(base.CreateCommand):
  """Create a backend bucket.

  *{command}* is used to create backend buckets. Backend buckets
  define Google Cloud Storage buckets that can serve content. URL
  maps define which requests are sent to which backend buckets.
  """

  BACKEND_BUCKET_ARG = None
  _support_regional_global_flags = False

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command."""
    parser.display_info.AddFormat(backend_buckets_flags.DEFAULT_LIST_FORMAT)
    backend_buckets_flags.AddUpdatableArgs(
        cls, parser, 'create', cls._support_regional_global_flags
    )
    backend_buckets_flags.REQUIRED_GCS_BUCKET_ARG.AddArgument(parser)
    parser.display_info.AddCacheUpdater(
        backend_buckets_flags.BackendBucketsCompleter)
    signed_url_flags.AddSignedUrlCacheMaxAge(parser, required=False)

    cdn_flags.AddCdnPolicyArgs(parser, 'backend bucket')

    backend_buckets_flags.AddCacheKeyExtendedCachingArgs(parser)
    backend_buckets_flags.AddCompressionMode(parser)
    backend_buckets_flags.AddLoadBalancingScheme(parser)

  def CreateBackendBucket(self, args):
    """Creates and returns the backend bucket."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    backend_buckets_ref = self.BACKEND_BUCKET_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)

    enable_cdn = args.enable_cdn or False

    backend_bucket = client.messages.BackendBucket(
        description=args.description,
        name=backend_buckets_ref.Name(),
        bucketName=args.gcs_bucket_name,
        enableCdn=enable_cdn,
    )

    backend_buckets_utils.ApplyCdnPolicyArgs(client, args, backend_bucket)

    if args.custom_response_header is not None:
      backend_bucket.customResponseHeaders = args.custom_response_header
    if (
        backend_bucket.cdnPolicy is not None
        and backend_bucket.cdnPolicy.cacheMode
        and args.enable_cdn is not False  # pylint: disable=g-bool-id-comparison
    ):
      backend_bucket.enableCdn = True

    if args.compression_mode is not None:
      backend_bucket.compressionMode = (
          client.messages.BackendBucket.CompressionModeValueValuesEnum(
              args.compression_mode
          )
      )

    if args.load_balancing_scheme is not None:
      backend_bucket.loadBalancingScheme = (
          client.messages.BackendBucket.LoadBalancingSchemeValueValuesEnum(
              args.load_balancing_scheme
          )
      )

    return backend_bucket

  def Run(self, args):
    """Issues the request necessary for creating a backend bucket."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    backend_bucket = self.CreateBackendBucket(args)

    if self._support_regional_global_flags:
      ref = backend_buckets_flags.GLOBAL_REGIONAL_BACKEND_BUCKET_ARG.ResolveAsResource(
          args,
          holder.resources,
          scope_lister=compute_flags.GetDefaultScopeLister(client),
          default_scope=compute_scope.ScopeEnum.GLOBAL
      )
      if ref.Collection() == 'compute.backendBuckets':
        requests = self._CreateGlobalRequests(backend_bucket, ref)
      elif ref.Collection() == 'compute.regionBackendBuckets':
        requests = self._CreateRegionalRequests(args, backend_bucket, ref)

      return client.MakeRequests(requests)

    backend_buckets_ref = self.BACKEND_BUCKET_ARG.ResolveAsResource(
        args, holder.resources)
    return client.MakeRequests(
        self._CreateGlobalRequests(backend_bucket, backend_buckets_ref)
    )

  def _CreateGlobalRequests(self, backend_bucket, backend_buckets_ref):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    request = client.messages.ComputeBackendBucketsInsertRequest(
        backendBucket=backend_bucket, project=backend_buckets_ref.project
    )
    return [(client.apitools_client.backendBuckets, 'Insert', request)]

  def _CreateRegionalRequests(self, args, backend_bucket, backend_buckets_ref):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    request = client.messages.ComputeRegionBackendBucketsInsertRequest(
        backendBucket=backend_bucket,
        project=backend_buckets_ref.project,
        region=args.region,
    )
    return [(client.apitools_client.regionBackendBuckets, 'Insert', request)]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class CreateBeta(Create):
  """Create a backend bucket.

  *{command}* is used to create backend buckets. Backend buckets
  define Google Cloud Storage buckets that can serve content. URL
  maps define which requests are sent to which backend buckets.
  """

  _support_regional_global_flags = False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class CreateAlpha(CreateBeta):
  """Create a backend bucket.

  *{command}* is used to create backend buckets. Backend buckets
  define Google Cloud Storage buckets that can serve content. URL
  maps define which requests are sent to which backend buckets.
  """
  _support_regional_global_flags = True
