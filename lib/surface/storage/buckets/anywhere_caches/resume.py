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
"""Implementation of resume command for resuming Anywhere Cache Instances."""

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Resume(base.Command):
  """Resume Anywhere Cache Instances of a bucket."""

  detailed_help = {
      'DESCRIPTION': """

      Resume operation could be used to revert the Paused and Disabled state.
      Once a paused/disabled cache is resumed, the cache will be set to
      RUNNING/CREATING state:
        1. RUNNING if the cache is active.
        2. CREATING if the cache is pending creation.
      """,
      'EXAMPLES': """

      The following command resume anywhere cache instance of bucket
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
    # TODO(b/303559351) : Implementation of resume command
    raise NotImplementedError
