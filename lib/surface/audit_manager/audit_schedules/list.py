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
"""Command to list Audit Schedules."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.audit_manager import audit_schedules
from googlecloudsdk.api_lib.audit_manager import constants
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.audit_manager import exception_utils
from googlecloudsdk.command_lib.audit_manager import flags
from googlecloudsdk.core import exceptions as core_exceptions

_DETAILED_HELP = {
    "DESCRIPTION": "List Audit Schedules.",
    "EXAMPLES": (
        """ \
        To list Audit Schedules in the `us-central1` region for project `123`, run:

          $ {command} --project=123 --location=us-central1
        """
    ),
}


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Audit Schedules."""

  detailed_help = _DETAILED_HELP
  api_version = constants.ApiVersion.V1

  @staticmethod
  def Args(parser):
    flags.AddProjectOrFolderOrOrganizationFlags(
        parser, "for which to list audit schedules"
    )
    flags.AddLocationFlag(parser, "audit schedules should be listed")
    parser.display_info.AddFormat("""
        table[all-box](
            name.basename():label=ID:wrap=10,
            complianceFramework:label=FRAMEWORK:wrap=10,
            displayName:label=DISPLAY_NAME:wrap=12,
            state:label=STATE:wrap=10,
            gcsUri:label=GCS_URI:wrap=10,
            reportFormat:label=REPORT_FORMAT:wrap=13,
            scheduleConfig:label=SCHEDULE_CONFIG:wrap=15,
            createTime:label=CREATE_TIME:wrap=11,
            updateTime:label=UPDATE_TIME:wrap=11,
            nextRunTime:label=NEXT_RUN_TIME:wrap=13,
            lastTriggerTime:label=LAST_TRIGGER_TIME:wrap=17,
            errorMessage:label=ERROR_MESSAGE:wrap=13
        )
    """)

  def Run(self, args):
    """Run the list command."""
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
      return client.List(
          scope,
          is_parent_folder=is_parent_folder,
          is_parent_organization=is_parent_organization,
          limit=args.limit,
          page_size=args.page_size,
      )

    except apitools_exceptions.HttpError as error:
      exc = exception_utils.AuditManagerError(error)
      core_exceptions.reraise(exc)


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List Audit Schedules."""

  api_version = constants.ApiVersion.V1_ALPHA
