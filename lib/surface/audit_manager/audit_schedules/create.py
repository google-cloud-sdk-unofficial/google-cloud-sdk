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
"""Command to create a new Audit Schedule."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.audit_manager import audit_schedules
from googlecloudsdk.api_lib.audit_manager import constants
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.audit_manager import exception_utils
from googlecloudsdk.command_lib.audit_manager import flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties

_DETAILED_HELP = {
    "DESCRIPTION": "Create a new Audit Schedule.",
    "EXAMPLES": (
        """ \
        To create an Audit Schedule in the `us-central1` region,
        for a project with ID `123` for compliance framework `fedramp_moderate` in `odf` format, run:

          $ {command} --project=123 --location=us-central1 --audit-schedule-id=my-schedule --compliance-framework=fedramp_moderate --report-format=odf --gcs-uri=gs://testbucketauditmanager --start-time="2026-03-01T00:00:00Z" --frequency=DAILY
        """
    ),
}


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create Audit Schedule."""

  detailed_help = _DETAILED_HELP
  api_version = constants.ApiVersion.V1

  @staticmethod
  def Args(parser):
    flags.AddProjectOrFolderOrOrganizationFlags(
        parser, "for which to create audit schedule"
    )
    flags.AddLocationFlag(parser, "the audit schedule should be created")
    flags.AddAuditScheduleIdFlag(parser)
    flags.AddComplianceFrameworkFlag(parser)
    flags.AddReportFormatFlag(parser)
    flags.AddDestinationFlags(parser)
    flags.AddScheduleConfigFlags(parser)
    flags.AddDisplayNameFlag(parser)
    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    """Run the create command."""
    is_parent_folder = args.folder is not None
    is_parent_organization = args.organization is not None

    if is_parent_folder:
      scope = "folders/{folder}".format(folder=args.folder)
    elif is_parent_organization:
      scope = "organizations/{organization}".format(
          organization=args.organization
      )
    else:
      scope = "projects/{project}".format(project=args.project)

    scope += "/locations/{location}".format(location=args.location)

    client = audit_schedules.AuditSchedulesClient(api_version=self.api_version)

    try:
      return client.Create(
          scope,
          args.audit_schedule_id,
          args.compliance_framework,
          report_format=args.report_format,
          gcs_uri=args.gcs_uri,
          start_time=args.start_time,
          frequency=args.frequency,
          end_time=getattr(args, "end_time", None),
          time_zone=getattr(args, "time_zone", None),
          display_name=getattr(args, "display_name", None),
          is_parent_folder=is_parent_folder,
          is_parent_organization=is_parent_organization,
      )

    except apitools_exceptions.HttpError as error:
      exc = exception_utils.AuditManagerError(error)

      if exc.has_error_info(exception_utils.ERROR_REASON_NOT_ENROLLED):
        exc.suggested_command_purpose = "enroll the resource"
        exc.suggested_command = (
            f"{flags.GetCommandPrefix(args.command_path)} enrollments add"
            f" {flags.GetProjectOrFolderOrOrganizationParam(args)}"
            f" {flags.GetEligibleGcsBucketParam(args)}"
        )
      elif exc.has_error_info(exception_utils.ERROR_REASON_PERMISSION_DENIED):
        role = "roles/auditmanager.admin"
        user = properties.VALUES.core.account.Get()
        exc.suggested_command_purpose = "grant permission"
        if is_parent_folder:
          command_prefix = (
              "gcloud resource-manager folders add-iam-policy-binding"
          )
        elif is_parent_organization:
          command_prefix = "gcloud organizations add-iam-policy-binding"
        else:
          command_prefix = "gcloud projects add-iam-policy-binding"
        exc.suggested_command = (
            f"{command_prefix}"
            f" {args.folder if is_parent_folder else args.organization if is_parent_organization else args.project}"
            f" --member=user:{user} --role {role}"
        )

      core_exceptions.reraise(exc)


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create Audit Schedule."""

  api_version = constants.ApiVersion.V1_ALPHA
