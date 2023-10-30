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
"""Implementation of list command to list Anywhere Cache Instances of bucket."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all Anywhere Cache Instances of a bucket."""

  detailed_help = {
      'DESCRIPTION': """

      List all cache instances of this bucket.
      """,
      'EXAMPLES': """

      The following command lists all anywhere cache instances of bucket
      ``gs://my-bucket'':

        $ {command} gs://my-bucket
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'url',
        type=str,
        nargs=1,
        help=(
            'Specifies the URL of the bucket for which anywhere cache instances'
            ' should be listed.'
        ),
    )

    flags.add_raw_display_flag(parser)
    flags.add_uri_support_to_list_commands(parser)

  def Run(self, args):
    # TODO(b/303559863) : Implementation of list command
    raise NotImplementedError
