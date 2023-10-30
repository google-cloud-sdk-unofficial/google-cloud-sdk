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
"""Implementation of describe command to get the Anywhere Cache Instance."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Returns details of Anywhere Cache Instance of a bucket."""

  detailed_help = {
      'DESCRIPTION': """

      Desribes a single Anywhere Cache instance if it exists.
      """,
      'EXAMPLES': """

      The following command describes Anywhere Cache Instance of bucket
      ``gs://my-bucket'' in ``asia-south2-b'' zone:

        $ {command} gs://my-bucket/asia-south2-b
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'id',
        type=str,
        nargs=1,
        help=(
            'Identifier for a Anywhere Cache instance. It is a combination of'
            ' bucket_name/zone.'
        ),
    )

    flags.add_raw_display_flag(parser)

  def Run(self, args):
    # TODO(b/303559468) : Implementation of describe command
    raise NotImplementedError
