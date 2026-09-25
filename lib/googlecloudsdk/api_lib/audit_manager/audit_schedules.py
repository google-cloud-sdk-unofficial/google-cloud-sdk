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
"""Utilities for Audit Manager API, Audit Schedule Endpoints."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.audit_manager import constants
from googlecloudsdk.api_lib.audit_manager import util
from googlecloudsdk.calliope import exceptions


class AuditSchedulesClient(object):
  """Client for Audit Schedules in Audit Manager API."""

  def __init__(
      self, api_version: constants.ApiVersion, client=None, messages=None
  ) -> None:
    self.client = client or util.GetClientInstance(api_version=api_version)
    self.messages = messages or util.GetMessagesModule(
        api_version=api_version, client=client
    )

    audit_report_format_enum = (
        self.messages.AuditSchedule.ReportFormatValueValuesEnum
    )
    self.report_format_map = {
        "odf": audit_report_format_enum.AUDIT_REPORT_FORMAT_ODF
    }

    frequency_enum = self.messages.ScheduleConfig.FrequencyValueValuesEnum
    self.frequency_map = {
        "daily": frequency_enum.DAILY,
        "weekly": frequency_enum.WEEKLY,
        "monthly": frequency_enum.MONTHLY,
        "quarterly": frequency_enum.QUARTERLY,
        "annually": frequency_enum.ANNUALLY,
    }

  def Create(
      self,
      parent: str,
      audit_schedule_id: str,
      compliance_framework: str,
      report_format: str,
      gcs_uri: str,
      start_time: str,
      frequency: str,
      end_time: str = None,
      time_zone: str = None,
      display_name: str = None,
      is_parent_folder: bool = False,
      is_parent_organization: bool = False,
  ):
    """Create an Audit Schedule."""
    if is_parent_folder and is_parent_organization:
      raise ValueError(
          "is_parent_folder and is_parent_organization are mutually exclusive."
      )

    schedule_config = self.messages.ScheduleConfig(
        startTime=start_time,
        frequency=self.frequency_map[frequency.lower()],
    )
    if end_time:
      schedule_config.endTime = end_time
    if time_zone:
      schedule_config.timeZone = time_zone

    audit_schedule = self.messages.AuditSchedule(
        gcsUri=gcs_uri,
        complianceFramework=compliance_framework,
        reportFormat=self.report_format_map[report_format.lower()],
        scheduleConfig=schedule_config,
    )
    if display_name:
      audit_schedule.displayName = display_name

    if is_parent_folder:
      service = self.client.folders_locations_auditSchedules
      req = (
          self.messages.AuditmanagerFoldersLocationsAuditSchedulesCreateRequest()
      )
    elif is_parent_organization:
      service = self.client.organizations_locations_auditSchedules
      req = (
          self.messages.AuditmanagerOrganizationsLocationsAuditSchedulesCreateRequest()
      )
    else:
      service = self.client.projects_locations_auditSchedules
      req = (
          self.messages.AuditmanagerProjectsLocationsAuditSchedulesCreateRequest()
      )

    req.parent = parent
    req.auditScheduleId = audit_schedule_id
    req.auditSchedule = audit_schedule
    return service.Create(req)

  def List(
      self,
      parent: str,
      is_parent_folder: bool = False,
      is_parent_organization: bool = False,
      limit=None,
      page_size=None,
  ):
    """List Audit Schedules."""
    if is_parent_folder and is_parent_organization:
      raise ValueError(
          "is_parent_folder and is_parent_organization are mutually exclusive."
      )

    if is_parent_folder:
      service = self.client.folders_locations_auditSchedules
      req = (
          self.messages.AuditmanagerFoldersLocationsAuditSchedulesListRequest()
      )
    elif is_parent_organization:
      service = self.client.organizations_locations_auditSchedules
      req = (
          self.messages.AuditmanagerOrganizationsLocationsAuditSchedulesListRequest()
      )
    else:
      service = self.client.projects_locations_auditSchedules
      req = (
          self.messages.AuditmanagerProjectsLocationsAuditSchedulesListRequest()
      )

    req.parent = parent
    return list_pager.YieldFromList(
        service,
        req,
        batch_size_attribute="pageSize",
        batch_size=page_size,
        limit=limit,
        field="auditSchedules",
    )

  def Update(
      self,
      name: str,
      state: str,
  ):
    """Update an Audit Schedule state (pause/resume)."""
    schedule_state_enum = self.messages.AuditSchedule.StateValueValuesEnum
    state_map = {
        "active": schedule_state_enum.SCHEDULE_STATE_ACTIVE,
        "paused": schedule_state_enum.SCHEDULE_STATE_PAUSED,
        "deleted": schedule_state_enum.SCHEDULE_STATE_DELETED,
    }

    audit_schedule = self.messages.AuditSchedule(
        name=name,
        state=state_map[state.lower()],
    )

    if name.startswith("folders/"):
      service = self.client.folders_locations_auditSchedules
      req = (
          self.messages.AuditmanagerFoldersLocationsAuditSchedulesPatchRequest()
      )
    elif name.startswith("organizations/"):
      service = self.client.organizations_locations_auditSchedules
      req = (
          self.messages.AuditmanagerOrganizationsLocationsAuditSchedulesPatchRequest()
      )
    elif name.startswith("projects/"):
      service = self.client.projects_locations_auditSchedules
      req = (
          self.messages.AuditmanagerProjectsLocationsAuditSchedulesPatchRequest()
      )
    else:
      raise exceptions.InvalidArgumentException(
          "name",
          "Audit schedule name must be of the form "
          "projects/{project}/locations/{location}/auditSchedules/{audit_schedule}, "
          "folders/{folder}/locations/{location}/auditSchedules/{audit_schedule}, or "
          "organizations/{organization}/locations/{location}/auditSchedules/{audit_schedule}.",
      )

    req.name = name
    req.auditSchedule = audit_schedule
    req.updateMask = "state"
    return service.Patch(req)
