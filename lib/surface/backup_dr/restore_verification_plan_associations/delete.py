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
"""Delete a specified Backup and DR Restore Verification Plan Association."""

from __future__ import annotations

from typing import Any

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import restore_verification_plan_associations
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete the specified restore verification plan association."""

  detailed_help = {
      'BRIEF': 'Delete a specific restore verification plan association.',
      'DESCRIPTION': (
          'Delete the specified restore verification plan association.'
      ),
      'EXAMPLES': (
          """\
        To delete a restore verification plan association `sample-association` under restore verification plan `sample-plan` in project `sample-project` and location `us-central1`, run:

          $ {command} sample-association --restore-verification-plan=sample-plan --project=sample-project --location=us-central1
        """
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddRestoreVerificationPlanAssociationResourceArg(
        parser,
        'Name of the restore verification plan association to delete.',
    )

  def Run(self, args: parser_extensions.Namespace) -> Any:
    """Deletes a RestoreVerificationPlanAssociation resource."""
    api_version = util.GetApiVersion(self.ReleaseTrack())
    client = restore_verification_plan_associations.RestoreVerificationPlanAssociationsClient(
        api_version=api_version
    )
    is_async = args.async_

    association = args.CONCEPTS.restore_verification_plan_association.Parse()

    console_io.PromptContinue(
        message=(
            f'The restore verification plan association [{association.Name()}]'
            ' will be deleted. You cannot undo this action.'
        ),
        default=True,
        cancel_on_no=True,
    )

    try:
      operation = client.Delete(association)
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT) from e

    if is_async:
      log.DeletedResource(
          association.RelativeName(),
          kind='restore verification plan association',
          is_async=True,
          details=util.ASYNC_OPERATION_MESSAGE.format(operation.name),
      )
      return operation

    response = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'Deleting restore verification plan association'
            f' [{association.RelativeName()}]. (This operation could take up to'
            ' 2 minutes.)'
        ),
        has_result=False,
    )
    log.DeletedResource(
        association.RelativeName(), kind='restore verification plan association'
    )
    return response
