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
"""Command to list control compliance summaries of a compliance report."""

from googlecloudsdk.api_lib.assured import compliance as apis
from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags

_DETAILED_HELP = {
    'DESCRIPTION': (
        'List the control compliance summaries of a Data Boundary framework '
        'compliance report.'
    ),
    'EXAMPLES': (
        """ \
        To list the control compliance summaries of compliance report
        `fedramp-high` of organization `123` in the `us-central1` location,
        run:

          $ {command} --compliance-report=fedramp-high --organization=123 --location=us-central1
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List control compliance summaries of a framework compliance report."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddListControlComplianceSummariesFlags(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(
        'table(control.basename():label=CONTROL,'
        ' displayName:label=DISPLAY_NAME,'
        ' overallEvaluationState:label=STATE,'
        ' totalFindingsCount:label=FINDINGS)'
    )

  def Run(self, args):
    """Run the list command."""
    report = args.CONCEPTS.compliance_report.Parse()
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=report.locationsId
    ):
      client = apis.ComplianceClient(release_track=self.ReleaseTrack())
      return client.ListControlComplianceSummaries(
          parent=report.RelativeName(),
          limit=args.limit,
          page_size=args.page_size or 50,
      )
