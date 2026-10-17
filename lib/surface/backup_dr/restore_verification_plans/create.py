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
"""Create a Restore Verification Plan."""

from __future__ import annotations

from typing import Any

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import restore_verification_plans
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.core import log


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Restore Verification Plan."""

  detailed_help = {
      'BRIEF': 'Create a restore verification plan.',
      'DESCRIPTION': '{description}',
      'EXAMPLES': (
          """\
        To create a restore verification plan with id `sample-plan` in location `us-central1`, run:

          $ {command} sample-plan --location=us-central1 --schedule="0 1 * * *" --time-zone="America/New_York"
        """
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddRestoreVerificationPlanResourceArg(parser, 'to create')
    parser.add_argument(
        '--schedule',
        required=True,
        type=str,
        help='Cron schedule for the restore verification plan.',
    )
    parser.add_argument(
        '--time-zone',
        required=False,
        default='UTC',
        type=str,
        help='Time zone for the schedule (e.g., America/New_York).',
    )
    parser.add_argument(
        '--description',
        type=str,
        help='Description of the restore verification plan.',
    )
    flags.AddLabels(parser)
    flags.AddRestoreVerificationPlanCleanupRuleFlags(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    """Creates a RestoreVerificationPlan resource."""
    api_version = util.GetApiVersion(self.ReleaseTrack())
    client = restore_verification_plans.RestoreVerificationPlansClient(
        api_version=api_version
    )
    is_async = args.async_

    plan_ref = args.CONCEPTS.restore_verification_plan.Parse()
    labels = args.labels

    try:
      operation = client.Create(
          plan_ref,
          schedule=args.schedule,
          time_zone=args.time_zone,
          description=args.description,
          labels=labels,
          success_cleanup_delay=args.success_cleanup_delay,
          skip_success_cleanup=args.skip_success_cleanup,
          failure_cleanup_delay=args.failure_cleanup_delay,
          skip_failure_cleanup=args.skip_failure_cleanup,
      )
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT) from e

    if is_async:
      log.CreatedResource(
          plan_ref.RelativeName(),
          kind='restore verification plan',
          is_async=True,
          details=util.ASYNC_OPERATION_MESSAGE.format(operation.name),
      )
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            f'Creating restore verification plan [{plan_ref.RelativeName()}]'
        ),
    )
    log.CreatedResource(
        plan_ref.RelativeName(), kind='restore verification plan'
    )
    return resource
