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
"""Cloud Backup and DR Restore Template Executions client."""

from __future__ import annotations

from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.backupdr.v1alpha import backupdr_v1alpha_messages


class RestoreTemplateExecutionsClient(util.BackupDrClientBase):
  """Cloud Backup and DR Restore Template Executions client.

  Attributes:
    service: The Backup and DR ProjectsLocationsRestoreTemplateExecutionsService
      instance.
  """

  def __init__(self, api_version: str = util.DEFAULT_API_VERSION):
    """Initializes the RestoreTemplateExecutionsClient.

    Args:
      api_version: The Backup and DR API version to target.
    """
    super().__init__(api_version=api_version)
    self.service = self.client.projects_locations_restoreTemplates_executions

  def Get(
      self, execution_resource: resources.Resource
  ) -> backupdr_v1alpha_messages.RestoreTemplateExecution:
    """Retrieves the specified RestoreTemplateExecution resource.

    Args:
      execution_resource: The parsed resource reference for the execution.

    Returns:
      The requested RestoreTemplateExecution protobuf message.
    """
    request = self.messages.BackupdrProjectsLocationsRestoreTemplatesExecutionsGetRequest(
        name=execution_resource.RelativeName()
    )
    return self.service.Get(request)

  def List(
      self,
      template_resource: resources.Resource,
      filter_expression: str | None = None,
      page_size: int | None = None,
      order_by: str | None = None,
  ) -> backupdr_v1alpha_messages.ListRestoreTemplateExecutionsResponse:
    """Lists RestoreTemplateExecution resources for the specified template.

    Args:
      template_resource: The parsed resource reference for the parent template.
      filter_expression: Optional filter expression to restrict results.
      page_size: Optional maximum number of executions to return per page.
      order_by: Optional sort order specification.

    Returns:
      The ListRestoreTemplateExecutionsResponse containing matching executions.
    """
    request = self.messages.BackupdrProjectsLocationsRestoreTemplatesExecutionsListRequest(
        parent=template_resource.RelativeName(),
        filter=filter_expression,
        pageSize=page_size,
        orderBy=order_by,
    )
    return self.service.List(request)

  def TriggerCleanup(
      self, execution_resource: resources.Resource
  ) -> backupdr_v1alpha_messages.Operation:
    """Triggers restore cleanup for the specified execution.

    Args:
      execution_resource: The parsed resource reference for the execution.

    Returns:
      The long-running Operation message for the cleanup request.
    """
    cleanup_req = self.messages.TriggerRestoreCleanupRequest()
    request = self.messages.BackupdrProjectsLocationsRestoreTemplatesExecutionsTriggerRestoreCleanupRequest(
        name=execution_resource.RelativeName(),
        triggerRestoreCleanupRequest=cleanup_req,
    )
    return self.service.TriggerRestoreCleanup(request)
