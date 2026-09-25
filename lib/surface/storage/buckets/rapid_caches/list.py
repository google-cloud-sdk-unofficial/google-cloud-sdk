# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Implementation of list command for Rapid Cache Ultra instances."""

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_util
from surface.storage.buckets.rapid_caches import describe

_DEFAULT_FORMAT = (
    'table(id:label=ID, zone:label=ZONE, cache_type:label=CACHE_TYPE,'
    ' state:label=STATE, ttl:label=TTL)'
)


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all Rapid Cache Ultra instances of a bucket."""

  detailed_help = {
      'DESCRIPTION': (
          """
      List all Rapid Cache Ultra instances of a bucket.
      """
      ),
      'EXAMPLES': (
          """
      The following command lists all Rapid Cache Ultra instances of bucket
      ``gs://my-bucket'':

        $ {command} gs://my-bucket
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'url',
        type=str,
        help=(
            'Specifies the URL of the bucket for which Rapid Cache Ultra'
            ' instances should be listed.'
        ),
    )
    flags.add_raw_display_flag(parser)
    parser.display_info.AddFormat(_DEFAULT_FORMAT)

  def Run(self, args):
    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_bucket(args.command_path, url)

    cache_resources = api_factory.get_api(url.scheme).list_rapid_caches(
        url.bucket_name
    )
    for cache_resource in cache_resources:
      yield resource_util.get_display_dict_for_resource(
          cache_resource,
          describe.RapidCacheDisplayTitlesAndDefaults,
          args.raw,
      )
