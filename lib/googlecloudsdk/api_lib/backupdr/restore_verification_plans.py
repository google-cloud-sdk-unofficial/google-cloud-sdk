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
"""Cloud Backup and DR Restore verification plans client."""

from __future__ import annotations

from collections.abc import Mapping

from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.command_lib.backupdr import util as command_util
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.backupdr.v1alpha import backupdr_v1alpha_messages


class RestoreVerificationPlansClient(util.BackupDrClientBase):
  """Cloud Backup and DR Restore Verification Plans client.

  Attributes:
    service: The Backup and DR ProjectsLocationsRestoreVerificationPlansService
      instance.
  """

  def __init__(self, api_version: str = util.DEFAULT_API_VERSION):
    """Initializes the RestoreVerificationPlansClient.

    Args:
      api_version: The API version to use.
    """
    super().__init__(api_version=api_version)
    self.service = self.client.projects_locations_restoreVerificationPlans

  def _format_delay(self, delay: int | str | None) -> str | None:
    """Formats a delay value into an API duration string."""
    if delay is None:
      return None
    if isinstance(delay, int):
      return command_util.ConvertIntToStr(delay)
    return str(delay)

  def Create(
      self,
      plan_resource: resources.Resource,
      schedule: str,
      time_zone: str | None = None,
      description: str | None = None,
      labels: Mapping[str, str] | None = None,
      success_cleanup_rule: (
          backupdr_v1alpha_messages.RestoreVerificationCleanupRule | None
      ) = None,
      failure_cleanup_rule: (
          backupdr_v1alpha_messages.RestoreVerificationCleanupRule | None
      ) = None,
      success_cleanup_delay: int | str | None = None,
      skip_success_cleanup: bool | None = None,
      failure_cleanup_delay: int | str | None = None,
      skip_failure_cleanup: bool | None = None,
  ) -> backupdr_v1alpha_messages.Operation:
    """Creates a new RestoreVerificationPlan resource.

    Args:
      plan_resource: The parsed RestoreVerificationPlan resource reference.
      schedule: Cron schedule expression for restore verification runs.
      time_zone: Time zone for the schedule.
      description: Optional human-readable description of the plan.
      labels: Optional key-value labels to attach to the plan.
      success_cleanup_rule: Preconstructed cleanup rule for successful
        verifications.
      failure_cleanup_rule: Preconstructed cleanup rule for failed
        verifications.
      success_cleanup_delay: Delay before cleaning up resources after a
        successful verification.
      skip_success_cleanup: Whether to skip cleanup after a successful
        verification.
      failure_cleanup_delay: Delay before cleaning up resources after a failed
        verification.
      skip_failure_cleanup: Whether to skip cleanup after a failed verification.

    Returns:
      The long-running Operation created by the API.
    """
    parent = plan_resource.Parent().RelativeName()
    plan_id = plan_resource.Name()
    labels_message = None
    if labels:
      labels_message = self.messages.RestoreVerificationPlan.LabelsValue(
          additionalProperties=[
              self.messages.RestoreVerificationPlan.LabelsValue.AdditionalProperty(
                  key=key, value=value
              )
              for key, value in labels.items()
          ]
      )

    if not success_cleanup_rule and (
        success_cleanup_delay is not None or skip_success_cleanup is not None
    ):
      success_cleanup_rule = self.messages.RestoreVerificationCleanupRule(
          cleanupDelay=self._format_delay(success_cleanup_delay),
          skipCleanup=skip_success_cleanup,
      )

    if not failure_cleanup_rule and (
        failure_cleanup_delay is not None or skip_failure_cleanup is not None
    ):
      failure_cleanup_rule = self.messages.RestoreVerificationCleanupRule(
          cleanupDelay=self._format_delay(failure_cleanup_delay),
          skipCleanup=skip_failure_cleanup,
      )

    plan = self.messages.RestoreVerificationPlan(
        schedule=schedule,
        timeZone=time_zone,
        description=description,
        labels=labels_message,
        successCleanupRule=success_cleanup_rule,
        failureCleanupRule=failure_cleanup_rule,
    )
    request = self.messages.BackupdrProjectsLocationsRestoreVerificationPlansCreateRequest(
        parent=parent,
        restoreVerificationPlan=plan,
        restoreVerificationPlanId=plan_id,
    )
    return self.service.Create(request)

  def Get(
      self, plan_resource: resources.Resource
  ) -> backupdr_v1alpha_messages.RestoreVerificationPlan:
    """Retrieves the specified RestoreVerificationPlan resource.

    Args:
      plan_resource: The parsed RestoreVerificationPlan resource reference.

    Returns:
      The requested RestoreVerificationPlan message.
    """
    request = self.messages.BackupdrProjectsLocationsRestoreVerificationPlansGetRequest(
        name=plan_resource.RelativeName()
    )
    return self.service.Get(request)

  def List(
      self,
      location_resource: resources.Resource,
      filter_expression: str | None = None,
      page_size: int | None = None,
      order_by: str | None = None,
  ) -> backupdr_v1alpha_messages.ListRestoreVerificationPlansResponse:
    """Lists RestoreVerificationPlan resources in the specified location.

    Args:
      location_resource: The parent location resource reference.
      filter_expression: Filter string to restrict returned plans.
      page_size: Maximum number of plans to return per page.
      order_by: Sort order expression for the returned plans.

    Returns:
      A ListRestoreVerificationPlansResponse message.
    """
    request = self.messages.BackupdrProjectsLocationsRestoreVerificationPlansListRequest(
        parent=location_resource.RelativeName(),
        filter=filter_expression,
        pageSize=page_size,
        orderBy=order_by,
    )
    return self.service.List(request)

  def Delete(
      self, plan_resource: resources.Resource, force: bool = False
  ) -> backupdr_v1alpha_messages.Operation:
    """Deletes the specified RestoreVerificationPlan resource.

    Args:
      plan_resource: The parsed RestoreVerificationPlan resource reference.
      force: If True, also deletes any associations under this plan.

    Returns:
      The long-running Operation created by the API.
    """
    request = self.messages.BackupdrProjectsLocationsRestoreVerificationPlansDeleteRequest(
        name=plan_resource.RelativeName(),
        force=force,
    )
    return self.service.Delete(request)
