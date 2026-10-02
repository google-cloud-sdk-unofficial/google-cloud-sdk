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
"""Update a Restore Template."""

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
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _resolve_hook_config(
    job_value: str | None,
    is_job_specified: bool,
    timeout_value: int | str | None,
    is_timeout_specified: bool,
    current_config: Any,
) -> tuple[str | None, str | None]:
  """Resolves updated Cloud Run job and timeout values for a restore hook.

  Args:
    job_value: The Cloud Run job flag value from parsed CLI arguments.
    is_job_specified: Whether the Cloud Run job flag was explicitly provided.
    timeout_value: The hook timeout flag value from parsed CLI arguments.
    is_timeout_specified: Whether the timeout flag was explicitly provided.
    current_config: The existing hook configuration message on the template.

  Returns:
    A tuple of (cloud_run_job, formatted_timeout).
  """
  job = (
      job_value
      if is_job_specified
      else (current_config.cloudRunJob if current_config else None)
  )
  timeout = (
      timeout_value
      if is_timeout_specified
      else (current_config.timeout if current_config else None)
  )
  if timeout is not None and not str(timeout).endswith('s'):
    timeout = f'{timeout}s'
  return job, str(timeout) if timeout is not None else None


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a Restore Template."""

  detailed_help = {
      'BRIEF': 'Update a restore template.',
      'DESCRIPTION': '{description}',
      'EXAMPLES': (
          """\
        To update a restore template `my-template` with a new description, run:

          $ {command} my-template --location=us-central1 --description="Updated template"
        """
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddRestoreTemplateResourceArg(parser, 'to update')
    parser.add_argument(
        '--description',
        type=str,
        help='Description of the restore template.',
    )
    flags.AddRestoreProperties(parser, required=False)
    labels_util.AddUpdateLabelsFlags(parser)
    flags.AddRestoreTemplateHookFlags(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    api_version = util.GetApiVersion(self.ReleaseTrack())
    client = restore_templates.RestoreTemplatesClient(api_version=api_version)
    is_async = args.async_

    template_ref = args.CONCEPTS.restore_template.Parse()
    current_template = client.Get(template_ref)

    labels_update = labels_util.ProcessUpdateArgsLazy(
        args,
        client.messages.RestoreTemplate.LabelsValue,
        lambda: current_template.labels,
    )

    update_mask = []
    template = client.messages.RestoreTemplate()

    if args.IsSpecified('description'):
      template.description = args.description
      update_mask.append('description')

    if labels_update.needs_update:
      template.labels = labels_update.labels
      update_mask.append('labels')

    if args.IsSpecified('restore_properties'):
      template.restoreProperties = client.ParseRestoreProperties(
          args.restore_properties
      )
      update_mask.append('restore_properties')

    if args.IsSpecified('pre_restore_cloud_run_job') or args.IsSpecified(
        'pre_restore_timeout'
    ):
      job, timeout = _resolve_hook_config(
          args.pre_restore_cloud_run_job,
          args.IsSpecified('pre_restore_cloud_run_job'),
          args.pre_restore_timeout,
          args.IsSpecified('pre_restore_timeout'),
          current_template.preRestoreConfig,
      )
      template.preRestoreConfig = client.messages.PreRestoreConfig(
          cloudRunJob=job, timeout=timeout
      )
      update_mask.append('pre_restore_config')

    if args.IsSpecified('post_restore_cloud_run_job') or args.IsSpecified(
        'post_restore_timeout'
    ):
      job, timeout = _resolve_hook_config(
          args.post_restore_cloud_run_job,
          args.IsSpecified('post_restore_cloud_run_job'),
          args.post_restore_timeout,
          args.IsSpecified('post_restore_timeout'),
          current_template.postRestoreConfig,
      )
      template.postRestoreConfig = client.messages.PostRestoreConfig(
          cloudRunJob=job, timeout=timeout
      )
      update_mask.append('post_restore_config')

    if args.IsSpecified('verification_cloud_run_job') or args.IsSpecified(
        'verification_timeout'
    ):
      job, timeout = _resolve_hook_config(
          args.verification_cloud_run_job,
          args.IsSpecified('verification_cloud_run_job'),
          args.verification_timeout,
          args.IsSpecified('verification_timeout'),
          current_template.verificationConfig,
      )
      template.verificationConfig = client.messages.VerificationConfig(
          cloudRunJob=job, timeout=timeout
      )
      update_mask.append('verification_config')

    update_mask_str = ','.join(update_mask)

    try:
      operation = client.Update(
          template_ref, template, update_mask=update_mask_str
      )
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT) from e

    if is_async:
      log.UpdatedResource(
          template_ref.RelativeName(),
          kind='restore template',
          is_async=True,
          details=util.ASYNC_OPERATION_MESSAGE.format(operation.name),
      )
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=f'Updating restore template [{template_ref.RelativeName()}]',
    )
    log.UpdatedResource(template_ref.RelativeName(), kind='restore template')
    return resource
