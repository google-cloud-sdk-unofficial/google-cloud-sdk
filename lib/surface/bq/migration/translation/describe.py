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
"""Implements command to describe a translation."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bq.migration import translation_utils as utils


@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class Describe(base.DescribeCommand):
  """Get the details or status of a submitted translation.

  ## EXAMPLES

  To get the details of a translation with ID
  `12345678-1234-1234-1234-1234567890ab` in location `us-central1`, run:

    $ {command} 12345678-1234-1234-1234-1234567890ab --location=us-central1
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'translation_id',
        metavar='TRANSLATION_ID',
        help='The translation ID to describe.',
    )
    parser.add_argument(
        '--location',
        required=True,
        help='The location of the translation.',
    )

  def Run(self, args):
    return utils.get_workflow(args.translation_id, args.location)
