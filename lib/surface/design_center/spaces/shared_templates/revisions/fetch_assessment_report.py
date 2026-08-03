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
"""Command to fetch the assessment report for a Shared Template Revision."""

from __future__ import annotations

import copy

from googlecloudsdk.api_lib.design_center import constants
from googlecloudsdk.api_lib.design_center import shared_template_revisions as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags

_DETAILED_HELP = {
    'DESCRIPTION': 'Fetch the assessment report of a shared template revision.',
    'EXAMPLES': (
        """ \
        To fetch the assessment report of the shared template revision `my-revision` in shared template `my-shared-template`, space `my-space`, project `my-project` and location `us-central1`, run:

          $ {command} my-revision --shared-template=my-shared-template --space=my-space --project=my-project --location=us-central1

        Or run:

          $ {command} projects/my-project/locations/us-central1/spaces/my-space/sharedTemplates/my-shared-template/revisions/my-revision
        """
    ),
    'API REFERENCE': constants.API_REFERENCE_ALPHA,
}

_DETAILED_HELP_GA = copy.deepcopy(_DETAILED_HELP)
_DETAILED_HELP_GA['API REFERENCE'] = constants.API_REFERENCE_GA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class FetchAssessmentReportAlpha(base.Command):
  """Fetch the assessment report of a shared template revision."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddSharedTemplateRevisionResourceArg(
        parser, verb='to fetch assessment report for'
    )

  def Run(self, args):
    """Run the fetch-assessment-report command."""
    client = apis.SharedTemplateRevisionsClient(
        release_track=self.ReleaseTrack()
    )
    revision_ref = args.CONCEPTS.revision.Parse()
    return client.FetchAssessmentReport(name=revision_ref.RelativeName())


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
@base.UniverseCompatible
class FetchAssessmentReportGA(FetchAssessmentReportAlpha):
  """Fetch the assessment report of a shared template revision."""

  detailed_help = _DETAILED_HELP_GA
