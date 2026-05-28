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
"""Command to generate an application's assessment report."""

from __future__ import annotations

import textwrap

from googlecloudsdk.api_lib.design_center import applications as apis
from googlecloudsdk.api_lib.design_center import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags
from googlecloudsdk.core import log


_DETAILED_HELP = {
    'DESCRIPTION': 'Generate assessment report of an application in a space.',
    'EXAMPLES': textwrap.dedent("""\
        To generate assessment report for the application my-application in space my-space, project
        my-project and location us-central1, run:

            $ {command} my-application --space=my-space --project=my-project --location=us-central1

        Or run:

            $ {command} projects/my-project/locations/us-central1/spaces/my-space/applications/my-application

        To generate assessment report for the application my-application in space my-space, project
        my-project and location us-central1 asynchronously, run:

            $ {command} my-application --space=my-space --project=my-project --location=us-central1 --async
        """),
}


def _AddArgs(parser):
  """Register flags for this command."""
  flags.AddApplicationResourceArg(parser, verb='to generate assessment report for')
  base.ASYNC_FLAG.AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class GenerateAssessmentReport(base.Command):
  """Generate an assessment report for a Design Center application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    _AddArgs(parser)

  def Run(self, args):
    """Executes the generate-assessment-report command."""
    release_track = self.ReleaseTrack()
    application_ref = args.CONCEPTS.application.Parse()
    app_client = apis.ApplicationsClient(release_track)
    short_app_name = application_ref.applicationsId

    log.status.Print(f'Request issued for: [{short_app_name}]')
    operation = app_client.GenerateAssessmentReport(
        name=application_ref.RelativeName(),
    )

    if args.async_:
      log.status.Print(f'Check operation [{operation.name}] for status.')
      return operation

    # Synchronous Polling Implementation
    return utils.WaitForOperationWithEmbeddedResult(
        app_client.client,
        operation,
        message=f'Waiting for operation [{operation.name}] to complete',
        release_track=release_track,
        max_wait_sec=600,
    )


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
@base.UniverseCompatible
class GenerateAssessmentReportGa(GenerateAssessmentReport):
  """Generate an assessment report for a Design Center application."""
  pass
