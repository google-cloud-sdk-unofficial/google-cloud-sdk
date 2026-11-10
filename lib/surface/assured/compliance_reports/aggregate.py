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
"""Command to aggregate a Data Boundary framework compliance report."""

from googlecloudsdk.api_lib.assured import compliance as apis
from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags
from googlecloudsdk.core.util import times

_DETAILED_HELP = {
    'DESCRIPTION': (
        'Get the aggregated Data Boundary framework compliance report over '
        'time.'
    ),
    'EXAMPLES': (
        """ \
        To aggregate compliance report `fedramp-high` of organization `123` in
        the `us-central1` location for September 2026, run:

          $ {command} fedramp-high --organization=123 --location=us-central1 --start-time=2026-09-01T00:00:00Z --end-time=2026-10-01T00:00:00Z
        """
    ),
}


def _FormatTime(value):
  return times.FormatDateTime(value) if value else None


@base.DefaultUniverseOnly
@base.ReleaseTracks(ReleaseTrack.ALPHA)
class Aggregate(base.Command):
  """Aggregate a Data Boundary framework compliance report over time."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddAggregateComplianceReportFlags(parser)

  def Run(self, args):
    """Run the aggregate command."""
    if (
        args.start_time
        and args.end_time
        and args.start_time > args.end_time
    ):
      raise exceptions.InvalidArgumentException(
          '--start-time', 'must not be later than --end-time.'
      )
    report = args.CONCEPTS.compliance_report.Parse()
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=report.locationsId
    ):
      client = apis.ComplianceClient(release_track=self.ReleaseTrack())
      return client.AggregateFrameworkComplianceReport(
          name=report.RelativeName(),
          start_time=_FormatTime(args.start_time),
          end_time=_FormatTime(args.end_time),
      )
