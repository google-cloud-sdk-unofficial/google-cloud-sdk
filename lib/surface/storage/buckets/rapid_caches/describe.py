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
"""Implementation of describe command for Rapid Cache Ultra instances."""

import collections

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import rapid_caches_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_util

RapidCacheDisplayTitlesAndDefaults = collections.namedtuple(
    'RapidCacheDisplayTitlesAndDefaults',
    (
        'admission_policy',
        'bucket',
        'cache_type',
        'create_time',
        'id',
        'ingest_on_write',
        'kind',
        'pending_update',
        'rapid_cache_id',
        'state',
        'ttl',
        'update_time',
        'zone',
    ),
)


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe a Rapid Cache Ultra instance."""

  detailed_help = {
      'DESCRIPTION': (
          """
      Describe a single Rapid Cache Ultra instance.
      """
      ),
      'EXAMPLES': (
          """
      The following command describes the Rapid Cache Ultra instance of bucket
      ``my-bucket'' having cache ID ``my-cache-id'':

        $ {command} my-bucket/my-cache-id
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'id',
        type=str,
        help=(
            'Identifier for a Rapid Cache Ultra instance. It is a combination'
            ' of bucket_name/cache_id. For example: test-bucket/my-cache-id.'
        ),
    )
    flags.add_raw_display_flag(parser)

  def Run(self, args):
    bucket_name, rapid_cache_id = (
        rapid_caches_util.validate_and_parse_rapid_cache_id(args.id)
    )

    result = api_factory.get_api(
        storage_url.ProviderPrefix.GCS
    ).get_rapid_cache(bucket_name, rapid_cache_id)

    return resource_util.get_display_dict_for_resource(
        result,
        RapidCacheDisplayTitlesAndDefaults,
        args.raw,
    )
