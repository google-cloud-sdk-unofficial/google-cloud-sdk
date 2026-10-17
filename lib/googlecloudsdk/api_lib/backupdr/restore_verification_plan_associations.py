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
"""Cloud Backup and DR Restore verification plan associations client."""

from __future__ import annotations

from collections.abc import Mapping

from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.backupdr.v1alpha import backupdr_v1alpha_messages


class RestoreVerificationPlanAssociationsClient(util.BackupDrClientBase):
  """Cloud Backup and DR Restore Verification Plan Associations client.

  Attributes:
    service: The Backup and DR
      ProjectsLocationsRestoreVerificationPlansAssociationsService instance.
  """

  def __init__(self, api_version: str = util.DEFAULT_API_VERSION):
    """Initializes the RestoreVerificationPlanAssociationsClient.

    Args:
      api_version: The API version to use.
    """
    super().__init__(api_version=api_version)
    self.service = (
        self.client.projects_locations_restoreVerificationPlans_associations
    )

  def Create(
      self,
      association_resource: resources.Resource,
      resource_type: str,
      restore_template: str,
      description: str | None = None,
      labels: Mapping[str, str] | None = None,
  ) -> backupdr_v1alpha_messages.Operation:
    """Creates a new RestoreVerificationPlanAssociation resource.

    Args:
      association_resource: The parsed RestoreVerificationPlanAssociation
        resource reference.
      resource_type: The target resource type for restore verification.
      restore_template: The relative resource name of the restore template to
        use.
      description: Optional human-readable description of the association.
      labels: Optional key-value labels to attach to the association.

    Returns:
      The long-running Operation created by the API.
    """
    parent = association_resource.Parent().RelativeName()
    association_id = association_resource.Name()
    labels_message = None
    if labels:
      labels_message = self.messages.RestoreVerificationPlanAssociation.LabelsValue(
          additionalProperties=[
              self.messages.RestoreVerificationPlanAssociation.LabelsValue.AdditionalProperty(
                  key=key, value=value
              )
              for key, value in labels.items()
          ]
      )
    association = self.messages.RestoreVerificationPlanAssociation(
        resourceType=resource_type,
        restoreTemplate=restore_template,
        description=description,
        labels=labels_message,
    )
    request = self.messages.BackupdrProjectsLocationsRestoreVerificationPlansAssociationsCreateRequest(
        parent=parent,
        restoreVerificationPlanAssociation=association,
        restoreVerificationPlanAssociationId=association_id,
    )
    return self.service.Create(request)

  def Get(
      self, association_resource: resources.Resource
  ) -> backupdr_v1alpha_messages.RestoreVerificationPlanAssociation:
    """Retrieves the specified RestoreVerificationPlanAssociation resource.

    Args:
      association_resource: The parsed RestoreVerificationPlanAssociation
        resource reference.

    Returns:
      The requested RestoreVerificationPlanAssociation message.
    """
    request = self.messages.BackupdrProjectsLocationsRestoreVerificationPlansAssociationsGetRequest(
        name=association_resource.RelativeName()
    )
    return self.service.Get(request)

  def List(
      self,
      plan_resource: resources.Resource,
      filter_expression: str | None = None,
      page_size: int | None = None,
      order_by: str | None = None,
  ) -> (
      backupdr_v1alpha_messages.ListRestoreVerificationPlanAssociationsResponse
  ):
    """Lists RestoreVerificationPlanAssociation resources under a plan.

    Args:
      plan_resource: The parent RestoreVerificationPlan resource reference.
      filter_expression: Filter string to restrict returned associations.
      page_size: Maximum number of associations to return per page.
      order_by: Sort order expression for the returned associations.

    Returns:
      A ListRestoreVerificationPlanAssociationsResponse message.
    """
    request = self.messages.BackupdrProjectsLocationsRestoreVerificationPlansAssociationsListRequest(
        parent=plan_resource.RelativeName(),
        filter=filter_expression,
        pageSize=page_size,
        orderBy=order_by,
    )
    return self.service.List(request)

  def Delete(
      self, association_resource: resources.Resource
  ) -> backupdr_v1alpha_messages.Operation:
    """Deletes the specified RestoreVerificationPlanAssociation resource.

    Args:
      association_resource: The parsed RestoreVerificationPlanAssociation
        resource reference.

    Returns:
      The long-running Operation created by the API.
    """
    request = self.messages.BackupdrProjectsLocationsRestoreVerificationPlansAssociationsDeleteRequest(
        name=association_resource.RelativeName()
    )
    return self.service.Delete(request)

  def Trigger(
      self,
      association_resource: resources.Resource,
      request_id: str | None = None,
  ) -> backupdr_v1alpha_messages.Operation:
    """Triggers an on-demand restore verification for the association.

    Args:
      association_resource: The parsed RestoreVerificationPlanAssociation
        resource reference.
      request_id: Optional idempotency UUID for the trigger request.

    Returns:
      The long-running Operation created by the API.
    """
    trigger_req = self.messages.TriggerRestoreVerificationRequest(
        requestId=request_id
    )
    request = self.messages.BackupdrProjectsLocationsRestoreVerificationPlansAssociationsTriggerRestoreVerificationRequest(
        name=association_resource.RelativeName(),
        triggerRestoreVerificationRequest=trigger_req,
    )
    return self.service.TriggerRestoreVerification(request)
