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
"""Command to generate a space's Terraform assessment report."""

from __future__ import annotations

import textwrap

from googlecloudsdk.api_lib.design_center import spaces as apis
from googlecloudsdk.api_lib.design_center import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': 'Generate Terraform assessment report in a space.',
    'EXAMPLES': textwrap.dedent("""\
        To generate Terraform assessment report for space my-space, project
        my-project and location us-central1, run:

            $ {command} my-space --location=us-central1 --project=my-project --terraform-plan=path/to/plan.json
        """),
}


def _AddArgs(parser):
  """Register flags for this command."""
  flags.AddGenerateTerraformAssessmentReportFlags(parser)
  base.ASYNC_FLAG.AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class GenerateTerraformAssessmentReport(base.Command):
  """Generate a Terraform assessment report in a design center space."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    _AddArgs(parser)

  def Run(self, args):
    """Executes the generate-terraform-assessment-report command."""
    release_track = self.ReleaseTrack()
    space_ref = args.CONCEPTS.space.Parse()
    space_client = apis.SpacesClient(release_track)
    short_space_name = space_ref.spacesId

    tf_plan_bytes = args.terraform_plan

    log.status.Print(f'Request issued for: [{short_space_name}]')
    operation = space_client.GenerateTerraformPlanAssessmentReport(
        name=space_ref.RelativeName(),
        terraform_plan=tf_plan_bytes,
        additional_frameworks=args.additional_frameworks,
    )

    if args.async_:
      log.status.Print(f'Check operation [{operation.name}] for status.')
      return operation

    return utils.WaitForOperationWithEmbeddedResult(
        space_client.client,
        operation,
        message=f'Waiting for operation [{operation.name}] to complete',
        release_track=release_track,
        max_wait_sec=600,
    )


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
@base.UniverseCompatible
class GenerateTerraformAssessmentReportGa(
    GenerateTerraformAssessmentReport
):
  """Generate a Terraform assessment report in a design center space."""

  pass
