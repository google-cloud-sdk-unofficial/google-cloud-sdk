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
"""Implementation of disable command for disabling Anywhere Cache Instances."""

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Disable(base.Command):
  """Disable Anywhere Cache Instances of a bucket."""

  detailed_help = {
      'DESCRIPTION': """

        Disables one or more Anywhere Cache instances.

        The cache instance will be set to DISABLED state. The existing entries
        can be read from the cache but new entries will not be written to the
        cache. The L4 SSD cache would not be deleted by the cache manager until
        the min TTL (1h) has been reached (cache instance is kept for at least
        1h). Google Cloud Storage defines the min TTL which is applied to all
        cache instances. Cach disablement could be canceled by using
        anywhere-caches resume command before the instance is deleted.
      """,
      'EXAMPLES': """

      The following command disable the anywhere cache instance for bucket
      ``gs://my-bucket'' in ``asia-south2-b'' zone:

        $ {command} gs://my-bucket/asia-south2-b
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
            ' bucket_name/zone.'
        ),
    )

  def Run(self, args):
    # TODO(b/303559351) : Implementation of disable command
    raise NotImplementedError
