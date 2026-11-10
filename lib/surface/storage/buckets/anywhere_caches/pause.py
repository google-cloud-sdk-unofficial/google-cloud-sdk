# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implementation of pause command to pause Anywhere Cache instances."""

from googlecloudsdk.calliope import base


@base.Deprecate(
    is_removed=True,
    warning=(
        'The `gcloud storage buckets anywhere-caches pause` command is'
        ' deprecated and will be removed on September 23, 2026. Pause'
        ' functionality will no longer be supported.'
    ),
    error=(
        'The `gcloud storage buckets anywhere-caches pause` command has been'
        ' removed. Pause functionality is no longer supported.'
    ),
)
@base.DefaultUniverseOnly
class Pause(base.Command):
  """Pause Anywhere Cache instances."""

  hints = base.CommandHint(read_only=False)

  detailed_help = {
      'DESCRIPTION': """

        The pause operation can be used to stop the data ingestion of a cache
        instance in RUNNING state (read-only cache) until the Resume is invoked.
      """,
      'EXAMPLES': """

      The following command pause the anywhere cache instance of bucket
      ``my-bucket'' having anywhere_cache_id ``my-cache-id'':

        $ {command} my-bucket/my-cache-id
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'id',
        type=str,
        nargs='+',
        help=(
            'Identifiers for a Anywhere Cache instance. They are combination of'
            ' bucket_name/anywhere_cache_id. For example :'
            ' test-bucket/my-cache-id.'
        ),
    )

  def Run(self, args):
    del args  # Unused; command is removed.
