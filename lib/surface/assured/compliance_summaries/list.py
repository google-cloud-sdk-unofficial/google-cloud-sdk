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
"""Command to list Data Boundary framework compliance summaries."""

from googlecloudsdk.api_lib.assured import compliance as apis
from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags

_DETAILED_HELP = {
    'DESCRIPTION': (
        'List the Data Boundary framework compliance summaries for an '
        'organization.'
    ),
    'EXAMPLES': (
        """ \
        To list the framework compliance summaries of organization `123` in
        the `us-central1` location, run:

          $ {command} --organization=123 --location=us-central1

        To return all available information for each summary, run:

          $ {command} --organization=123 --location=us-central1 --view=full
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Data Boundary framework compliance summaries."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddListFrameworkComplianceSummariesFlags(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(
        'table(framework.basename():label=FRAMEWORK,'
        ' frameworkDisplayName:label=DISPLAY_NAME,'
        ' frameworkType:label=TYPE,'
        ' controlAssessmentDetails.passingControls:label=PASSING_CONTROLS,'
        ' controlAssessmentDetails.failingControls:label=FAILING_CONTROLS)'
    )

  def Run(self, args):
    """Run the list command."""
    location = args.CONCEPTS.location.Parse()
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=location.locationsId
    ):
      client = apis.ComplianceClient(release_track=self.ReleaseTrack())
      return client.ListFrameworkComplianceSummaries(
          parent=location.RelativeName(),
          view=args.view,
          limit=args.limit,
          page_size=args.page_size or 50,
      )
