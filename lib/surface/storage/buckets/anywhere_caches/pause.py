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
"""Implementation of pause command to pause Anywhere Cache Instances."""

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Pause(base.Command):
  """Pause Anywhere Cache Instances of a bucket."""

  detailed_help = {
      'DESCRIPTION': """

        The pause operation can be used to stop the data ingestion of a cache
        instance in RUNNING state (read-only cache) until the Resume is invoked.
      """,
      'EXAMPLES': """

      The following command pause the anywhere cache instance of bucket
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
    # TODO(b/303559351) : Implementation of pause command
    raise NotImplementedError
