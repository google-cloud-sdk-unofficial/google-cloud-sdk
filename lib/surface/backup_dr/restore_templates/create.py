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
"""Create a Restore Template."""

from __future__ import annotations

from typing import Any

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import restore_templates
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Restore Template."""

  detailed_help = {
      'BRIEF': 'Create a restore template.',
      'DESCRIPTION': '{description}',
      'EXAMPLES': (
          """\
        To create a restore template `my-template` in location `us-central1`, run:

          $ {command} my-template --location=us-central1 --resource-type="compute.googleapis.com/Instance" --data-source="projects/my-project/locations/us-central1/backupVaults/my-vault/dataSources/my-ds" --restore-properties='{"name": "test-vm", "machineType": "e2-medium"}'
        """  # gcloud-disable-gdu-domain
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddRestoreTemplateResourceArg(parser, 'to create')
    parser.add_argument(
        '--resource-type',
        required=True,
        type=str,
        help=(
            'The type of the Google Cloud resource (e.g.,'
            ' compute.googleapis.com/Instance).'  # gcloud-disable-gdu-domain
        ),
    )
    flags.AddDataSource(parser, required=True)
    flags.AddRestoreProperties(parser, required=True)
    parser.add_argument(
        '--description',
        type=str,
        help='Description of the restore template.',
    )
    flags.AddLabels(parser)
    flags.AddRestoreTemplateHookFlags(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    api_version = util.GetApiVersion(self.ReleaseTrack())
    client = restore_templates.RestoreTemplatesClient(api_version=api_version)
    is_async = args.async_

    template_ref = args.CONCEPTS.restore_template.Parse()
    labels = args.labels

    if args.pre_restore_timeout and not args.pre_restore_cloud_run_job:
      raise calliope_exceptions.RequiredArgumentException(
          '--pre-restore-cloud-run-job',
          '--pre-restore-cloud-run-job is required when specifying'
          ' --pre-restore-timeout.',
      )
    if args.post_restore_timeout and not args.post_restore_cloud_run_job:
      raise calliope_exceptions.RequiredArgumentException(
          '--post-restore-cloud-run-job',
          '--post-restore-cloud-run-job is required when specifying'
          ' --post-restore-timeout.',
      )
    if args.verification_timeout and not args.verification_cloud_run_job:
      raise calliope_exceptions.RequiredArgumentException(
          '--verification-cloud-run-job',
          '--verification-cloud-run-job is required when specifying'
          ' --verification-timeout.',
      )

    try:
      operation = client.Create(
          template_ref,
          resource_type=args.resource_type,
          data_source=args.data_source,
          restore_properties=args.restore_properties,
          description=args.description,
          labels=labels,
          pre_restore_cloud_run_job=args.pre_restore_cloud_run_job,
          pre_restore_timeout=args.pre_restore_timeout,
          post_restore_cloud_run_job=args.post_restore_cloud_run_job,
          post_restore_timeout=args.post_restore_timeout,
          verification_cloud_run_job=args.verification_cloud_run_job,
          verification_timeout=args.verification_timeout,
      )
    except (
        ValueError,
        yaml.YAMLParseError,
        arg_parsers.ArgumentTypeError,
    ) as e:
      raise calliope_exceptions.InvalidArgumentException(
          '--restore-properties', str(e)
      ) from e
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT) from e

    if is_async:
      log.CreatedResource(
          template_ref.RelativeName(),
          kind='restore template',
          is_async=True,
          details=util.ASYNC_OPERATION_MESSAGE.format(operation.name),
      )
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=f'Creating restore template [{template_ref.RelativeName()}]',
    )
    log.CreatedResource(template_ref.RelativeName(), kind='restore template')
    return resource
