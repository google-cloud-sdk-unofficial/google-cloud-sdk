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
"""Trigger Restore Cleanup for a Restore Template Execution."""

from __future__ import annotations

from typing import Any

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import restore_template_executions
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
class TriggerRestoreCleanup(base.Command):
  """Trigger restore cleanup for a restore template execution."""

  detailed_help = {
      'BRIEF': 'Trigger restore cleanup for a restore template execution.',
      'DESCRIPTION': '{description}',
      'EXAMPLES': (
          """\
        To trigger restore cleanup for execution `my-exec` under template `my-template` in location `us-central1`, run:

          $ {command} my-exec --restore-template=my-template --location=us-central1
        """
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddRestoreTemplateExecutionResourceArg(
        parser, 'to trigger restore cleanup for'
    )

  def Run(self, args: parser_extensions.Namespace) -> Any:
    api_version = util.GetApiVersion(self.ReleaseTrack())
    client = restore_template_executions.RestoreTemplateExecutionsClient(
        api_version=api_version
    )
    is_async = args.async_

    execution_ref = args.CONCEPTS.restore_template_execution.Parse()

    try:
      operation = client.TriggerCleanup(execution_ref)
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT) from e

    if is_async:
      log.status.Print(
          'Trigger restore cleanup in progress for restore template execution'
          f' [{execution_ref.RelativeName()}]. Run [backup-dr operations'
          f' describe {operation.name}] to check the status of this operation.'
      )
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'Triggering restore cleanup for restore template execution'
            f' [{execution_ref.RelativeName()}]'
        ),
        has_result=False,
    )
    log.status.Print(
        'Triggered restore cleanup for restore template execution'
        f' [{execution_ref.RelativeName()}].'
    )
    return resource
