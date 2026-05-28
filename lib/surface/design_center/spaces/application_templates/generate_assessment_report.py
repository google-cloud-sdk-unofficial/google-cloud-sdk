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
"""Command to generate an assessment report for an Application Template."""


from __future__ import annotations

import argparse

from googlecloudsdk.api_lib.design_center import application_templates as apis
from googlecloudsdk.api_lib.design_center import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags
from googlecloudsdk.core import log


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To generate an assessment report for the application template `my-template` in
        space `my-space` and location `us-central1`, run:

            $ {command} my-template --space=my-space --location=us-central1

        To run the assessment using a specific service account, run:

            $ {command} my-template --space=my-space --location=us-central1
              --service-account=my-svc-account@my-project.iam.gserviceaccount.com
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
@base.UniverseCompatible
class GenerateAssessmentReportGA(base.Command):
  """Generate a best practice assessment report generator for an application template."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddApplicationTemplateResourceArg(
        parser, verb='to generate an assessment report for'
    )
    flags.AddGenerateAssessmentReportFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args: argparse.Namespace) -> object:
    """Run the generate-assessment-report command."""
    release_track = self.ReleaseTrack()
    client = apis.ApplicationTemplatesClient(release_track)
    app_template_ref = args.CONCEPTS.application_template.Parse()

    operation = client.GenerateAssessmentReport(
        name=app_template_ref.RelativeName(),
        service_account=args.service_account)

    if args.async_:
      log.status.Print(f'Check operation [{operation.name}] for status.')
      return operation

    # Synchronous Polling Implementation
    return utils.WaitForOperationWithEmbeddedResult(
        client.client,
        operation,
        message='Waiting for assessment report generation to complete',
        release_track=release_track,
        max_wait_sec=600)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class GenerateAssessmentReportAlpha(base.Command):
  """Generate a best practice assessment report generator for an application template."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddApplicationTemplateResourceArg(
        parser, verb='to generate an assessment report for'
    )
    flags.AddGenerateAssessmentReportFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the generate-assessment-report command."""
    release_track = self.ReleaseTrack()
    client = apis.ApplicationTemplatesClient(release_track)
    app_template_ref = args.CONCEPTS.application_template.Parse()

    operation = client.GenerateAssessmentReport(
        name=app_template_ref.RelativeName(),
        service_account=args.service_account)

    if args.async_:
      log.status.Print(f'Check operation [{operation.name}] for status.')
      return operation

    # Synchronous Polling Implementation
    return utils.WaitForOperationWithEmbeddedResult(
        client.client,
        operation,
        message='Waiting for assessment report generation to complete',
        release_track=release_track,
        max_wait_sec=600)
