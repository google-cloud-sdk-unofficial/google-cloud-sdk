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
"""Run a Restore Template."""

from __future__ import annotations

from typing import Any

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import restore_templates
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
class Run(base.Command):
  """Run a Restore Template."""

  detailed_help = {
      'BRIEF': 'Run a restore template on-demand.',
      'DESCRIPTION': '{description}',
      'EXAMPLES': (
          """\
        To run a restore template `my-template` in location `us-central1`, run:

          $ {command} my-template --location=us-central1

        To run with a specific backup:

          $ {command} my-template --location=us-central1 --backup="projects/p/locations/l/backupVaults/v/dataSources/ds/backups/b"
        """
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddRestoreTemplateResourceArg(parser, 'to run')
    flags.AddRunRestoreTemplateBackupFlag(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    api_version = util.GetApiVersion(self.ReleaseTrack())
    client = restore_templates.RestoreTemplatesClient(api_version=api_version)
    is_async = args.async_

    template_ref = args.CONCEPTS.restore_template.Parse()

    try:
      operation = client.Run(template_ref, backup=args.backup)
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT) from e

    if is_async:
      log.status.Print(
          'Run in progress for restore template'
          f' [{template_ref.RelativeName()}]. Run [backup-dr operations'
          f' describe {operation.name}] to check the status of this operation.'
      )
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=f'Running restore template [{template_ref.RelativeName()}]',
        has_result=False,
    )
    log.status.Print(f'Ran restore template [{template_ref.RelativeName()}].')
    return resource
