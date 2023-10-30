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
"""Implementation of update command for updating Anywhere Cache Instances."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update Anywhere Cache Instances of a bucket."""

  detailed_help = {
      'DESCRIPTION': """

      Update one or more Anywhere Cache instances. A cache instance can be
      updated if its state is created or pending creation.
      """,
      'EXAMPLES': """

      The following command updates cache entry's ttl, and admisson policy of
      anywhere cache instance of bucket gs://my-bucket in ``asia-south2-b''
      zone.

        $ {command} gs://my-bucket/asia-south2-b --ttl=6h --admission-policy='ADMIT_ON_SECOND_MISS'

      The following command updates cache entry's ttl of anywhere cache instance
      of bucket ``gs://my-bucket'', and ``gs://my-bucket-2'' in
      ``asia-south2-b'' zone.

        $ {command} gs://my-bucket/asia-south2-b gs://my-bucket-2/asia-south2-b --ttl=6h
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'id',
        type=str,
        nargs='+',
        help=(
            'Identifiers for a Anywhere Cache Instance.They are combination of'
            ' bucket_name/zone.'
        ),
    )

    parser.add_argument(
        '--ttl',
        type=arg_parsers.Duration(),
        help='Cache entry time-to-live. Default to 24h if not provided.',
    )

    flags.add_admission_policy_flag(parser)

  def Run(self, args):
    # TODO(b/303559100) : Implementation of update command
    raise NotImplementedError
