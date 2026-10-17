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
"""Creates Backup and DR Restore Verification Plan Association."""

from __future__ import annotations

from typing import Any

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import restore_verification_plan_associations
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a new restore verification plan association."""

  detailed_help = {
      'BRIEF': 'Creates a new restore verification plan association.',
      'DESCRIPTION': (
          'Create a new restore verification plan association in the project.'
      ),
      'EXAMPLES': (
          """\
        To create a new restore verification plan association `sample-association` under restore verification plan `sample-plan` in project `sample-project` and location `us-central1` for resource type `compute.googleapis.com/Instance` with restore template `projects/sample-project/locations/us-central1/restoreTemplates/sample-template`, run:

          $ {command} sample-association --restore-verification-plan=sample-plan --project=sample-project --location=us-central1 --resource-type=compute.googleapis.com/Instance --restore-template=projects/sample-project/locations/us-central1/restoreTemplates/sample-template
        """  # gcloud-disable-gdu-domain
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddCreateRestoreVerificationPlanAssociationFlags(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    """Creates a RestoreVerificationPlanAssociation resource."""
    api_version = util.GetApiVersion(self.ReleaseTrack())
    client = restore_verification_plan_associations.RestoreVerificationPlanAssociationsClient(
        api_version=api_version
    )
    is_async = args.async_

    association = args.CONCEPTS.restore_verification_plan_association.Parse()
    raw_plan = args.restore_verification_plan
    if raw_plan and '/' in raw_plan:
      plan_ref = resources.REGISTRY.Parse(
          raw_plan,
          params={'projectsId': association.projectsId},
          collection='backupdr.projects.locations.restoreVerificationPlans',
      )
      if association.locationsId != plan_ref.locationsId:
        raise calliope_exceptions.InvalidArgumentException(
            '--location',
            f'The location [{association.locationsId}] does not match the'
            ' parent restore-verification-plan location'
            f' [{plan_ref.locationsId}].',
        )
      association = resources.REGISTRY.Parse(
          association.Name(),
          params={
              'projectsId': association.projectsId,
              'locationsId': association.locationsId,
              'restoreVerificationPlansId': plan_ref.Name(),
          },
          collection=(
              'backupdr.projects.locations.restoreVerificationPlans.associations'
          ),
      )
    if (
        args.IsSpecified('location')
        and association.locationsId != args.location
    ):
      raise calliope_exceptions.InvalidArgumentException(
          '--location',
          f'The location [{args.location}] does not match the resource'
          f' location [{association.locationsId}].',
      )

    resource_type = args.resource_type
    restore_template_ref = args.CONCEPTS.restore_template.Parse()
    if (
        restore_template_ref
        and restore_template_ref.locationsId != association.locationsId
    ):
      raise calliope_exceptions.InvalidArgumentException(
          '--restore-template',
          f'The location [{restore_template_ref.locationsId}] does not match'
          f' the association location [{association.locationsId}].',
      )
    restore_template = restore_template_ref.RelativeName()
    description = args.description
    labels = args.labels

    try:
      operation = client.Create(
          association,
          resource_type=resource_type,
          restore_template=restore_template,
          description=description,
          labels=labels,
      )
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT) from e

    if is_async:
      log.CreatedResource(
          association.RelativeName(),
          kind='restore verification plan association',
          is_async=True,
          details=util.ASYNC_OPERATION_MESSAGE.format(operation.name),
      )
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'Creating restore verification plan association'
            f' [{association.RelativeName()}]. (This operation could take up to'
            ' 2 minutes.)'
        ),
    )
    log.CreatedResource(
        association.RelativeName(), kind='restore verification plan association'
    )
    return resource
