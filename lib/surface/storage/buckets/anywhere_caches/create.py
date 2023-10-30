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
"""Implementation of create command for creating Anywhere Cache Instances."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create Anywhere Cache Instances for a bucket."""

  detailed_help = {
      'DESCRIPTION': """

      Create Anywhere Cache instances.
      Only one cache instance per zone can be created for each bucket.
      """,
      'EXAMPLES': """

      The following command creates an anywhere cache instance for bucket
      in ``asia-south2-b'' zone:

        $ {command} gs://my-bucket asia-south2-b

      The following command creates anywhere cache instances for bucket
      in ``asia-south2-b'', and ``asia-east1-a'' zone:

        $ {command} gs://my-bucket asia-south2-b asia-east1-a

      The following command creates an anywhere cache instance for bucket
      in ``asia-south2-b'' zone, with ttl for cache entry as 6 hours, and
      admission policy as ``ADMIT_ON_SECOND_MISS'':

        $ {command} gs://my-bucket asia-south2-b --ttl=6h --admission-policy='ADMIT_ON_SECOND_MISS'
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'url',
        type=str,
        nargs=1,
        help=(
            'Specifies the URL of the bucket where the Anywhere Cache should be'
            ' created.'
        ),
    )

    parser.add_argument(
        'zone',
        type=str,
        nargs='+',
        help=(
            'Specifies the name of the zonal locations where the Anywhere Cache'
            ' should be created.'
        ),
    )

    parser.add_argument(
        '--ttl',
        type=arg_parsers.Duration(),
        help='Cache entry time-to-live. Default to 24h if not provided.',
    )

    flags.add_admission_policy_flag(parser)

  def Run(self, args):
    # TODO(b/303559466) : Implementation of create command
    raise NotImplementedError
