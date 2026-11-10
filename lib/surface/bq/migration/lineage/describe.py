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
"""Implements command to describe a lineage job."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bq.migration import translation_utils as utils


@base.Hidden
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class Describe(base.DescribeCommand):
  """Get the details or status of a lineage job.

  When the job has finished, the URL of the web app that visualizes the
  lineage is in the lineage task's
  `taskResult.taskOutputs.LINEAGE.lineageOutput.webappUri`. Opening the web app
  requires the `bigquerymigration.lineageDbs.query` IAM permission.

  ## EXAMPLES

  To get the details of a lineage job with ID
  `12345678-1234-1234-1234-1234567890ab` in location `us`, run:

    $ {command} 12345678-1234-1234-1234-1234567890ab --location=us
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'lineage_id',
        metavar='LINEAGE_ID',
        help='The ID of the lineage job to describe.',
    )
    parser.add_argument(
        '--location',
        required=True,
        help='The location of the lineage job.',
    )

  def Run(self, args):
    return utils.get_workflow(args.lineage_id, args.location)
