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
"""Cloud Backup and DR Restore Templates client."""

from __future__ import annotations

from collections.abc import Mapping
import os
from typing import Any

from apitools.base.py import encoding
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.backupdr import util as command_util
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.generated_clients.apis.backupdr.v1alpha import backupdr_v1alpha_messages


class RestoreTemplatesClient(util.BackupDrClientBase):
  """Cloud Backup and DR Restore Templates client.

  Attributes:
    service: The Backup and DR ProjectsLocationsRestoreTemplatesService
      instance.
  """

  def __init__(self, api_version: str = util.DEFAULT_API_VERSION):
    """Initializes the RestoreTemplatesClient.

    Args:
      api_version: The Backup and DR API version to target.
    """
    super().__init__(api_version=api_version)
    self.service = self.client.projects_locations_restoreTemplates

  def ParseRestoreProperties(
      self,
      restore_properties: (
          Mapping[str, Any]
          | str
          | backupdr_v1alpha_messages.RestoreTemplate.RestorePropertiesValue
          | None
      ),
  ) -> backupdr_v1alpha_messages.RestoreTemplate.RestorePropertiesValue | None:
    """Parses and converts restore_properties into a RestorePropertiesValue message.

    Supports inline JSON/YAML strings, @-prefixed file paths,
    yaml:/json: prefixed strings, direct paths to JSON/YAML files, or mappings.

    Args:
      restore_properties: The restore properties configuration to parse, or None
        if no restore properties were provided.

    Returns:
      The parsed RestorePropertiesValue protobuf message, or None if input is
      None.

    Raises:
      ValueError: If restore_properties cannot be parsed into a mapping.
    """
    if restore_properties is None:
      return None
    if isinstance(
        restore_properties, self.messages.RestoreTemplate.RestorePropertiesValue
    ):
      return restore_properties
    if isinstance(restore_properties, str):
      if restore_properties.startswith('@'):
        loaded = arg_parsers.FileContents()(restore_properties[1:])
      elif restore_properties.startswith(('json:', 'yaml:')):
        _, _, content = restore_properties.partition(':')
        content_stripped = content.strip()
        if content_stripped.startswith('@'):
          loaded = arg_parsers.FileContents()(content_stripped[1:])
        elif os.path.exists(content_stripped):
          loaded = arg_parsers.FileContents()(content_stripped)
        else:
          loaded = content
      elif os.path.exists(restore_properties):
        loaded = arg_parsers.FileContents()(restore_properties)
      else:
        loaded = restore_properties
      restore_properties = yaml.load(loaded)
    if isinstance(restore_properties, Mapping):
      return encoding.PyValueToMessage(
          self.messages.RestoreTemplate.RestorePropertiesValue,
          dict(restore_properties),
      )
    raise ValueError(
        'Invalid restore-properties format. Expected dict or JSON/YAML'
        ' string/file.'
    )

  def _FormatTimeout(self, timeout: int | str | None) -> str | None:
    if timeout is None:
      return None
    if isinstance(timeout, int):
      return command_util.ConvertIntToStr(timeout)
    return str(timeout)

  def Create(
      self,
      template_resource: resources.Resource,
      resource_type: str,
      backup_source: str | None = None,
      restore_properties: (
          Mapping[str, Any]
          | str
          | backupdr_v1alpha_messages.RestoreTemplate.RestorePropertiesValue
          | None
      ) = None,
      description: str | None = None,
      labels: Mapping[str, str] | None = None,
      pre_restore_cloud_run_job: str | None = None,
      pre_restore_timeout: int | str | None = None,
      post_restore_cloud_run_job: str | None = None,
      post_restore_timeout: int | str | None = None,
      verification_cloud_run_job: str | None = None,
      verification_timeout: int | str | None = None,
      data_source: str | None = None,
  ) -> backupdr_v1alpha_messages.Operation:
    """Creates a new RestoreTemplate resource.

    Args:
      template_resource: The parsed resource reference for the restore template.
      resource_type: The Google Cloud resource type being restored.
      backup_source: Deprecated alias for the data source resource name.
      restore_properties: Configuration properties for the restored workload.
      description: Optional human-readable description of the template.
      labels: Optional key-value labels to attach to the template.
      pre_restore_cloud_run_job: Optional Cloud Run job to execute before
        restoring.
      pre_restore_timeout: Optional timeout for the pre-restore Cloud Run job.
      post_restore_cloud_run_job: Optional Cloud Run job to execute after
        restoring.
      post_restore_timeout: Optional timeout for the post-restore Cloud Run job.
      verification_cloud_run_job: Optional Cloud Run job to execute for
        verification.
      verification_timeout: Optional timeout for the verification Cloud Run job.
      data_source: The full resource name of the data source to select backups
        from.

    Returns:
      The long-running Operation message for the creation request.
    """
    parent = template_resource.Parent().RelativeName()
    template_id = template_resource.Name()
    labels_message = None
    if labels:
      labels_message = self.messages.RestoreTemplate.LabelsValue(
          additionalProperties=[
              self.messages.RestoreTemplate.LabelsValue.AdditionalProperty(
                  key=key, value=value
              )
              for key, value in labels.items()
          ]
      )

    source = data_source or backup_source
    backup_selection_config = self.messages.BackupSelectionConfig(
        dataSource=source,
    )

    pre_restore_config = None
    if pre_restore_cloud_run_job or pre_restore_timeout is not None:
      pre_restore_config = self.messages.PreRestoreConfig(
          cloudRunJob=pre_restore_cloud_run_job,
          timeout=self._FormatTimeout(pre_restore_timeout),
      )

    post_restore_config = None
    if post_restore_cloud_run_job or post_restore_timeout is not None:
      post_restore_config = self.messages.PostRestoreConfig(
          cloudRunJob=post_restore_cloud_run_job,
          timeout=self._FormatTimeout(post_restore_timeout),
      )

    verification_config = None
    if verification_cloud_run_job or verification_timeout is not None:
      verification_config = self.messages.VerificationConfig(
          cloudRunJob=verification_cloud_run_job,
          timeout=self._FormatTimeout(verification_timeout),
      )

    restore_props_msg = self.ParseRestoreProperties(restore_properties)

    template = self.messages.RestoreTemplate(
        resourceType=resource_type,
        backupSelectionConfig=backup_selection_config,
        restoreProperties=restore_props_msg,
        description=description,
        labels=labels_message,
        preRestoreConfig=pre_restore_config,
        postRestoreConfig=post_restore_config,
        verificationConfig=verification_config,
    )

    request = (
        self.messages.BackupdrProjectsLocationsRestoreTemplatesCreateRequest(
            parent=parent,
            restoreTemplate=template,
            restoreTemplateId=template_id,
        )
    )
    return self.service.Create(request)

  def Get(
      self, template_resource: resources.Resource
  ) -> backupdr_v1alpha_messages.RestoreTemplate:
    """Retrieves the specified RestoreTemplate resource.

    Args:
      template_resource: The parsed resource reference for the restore template.

    Returns:
      The requested RestoreTemplate protobuf message.
    """
    request = self.messages.BackupdrProjectsLocationsRestoreTemplatesGetRequest(
        name=template_resource.RelativeName()
    )
    return self.service.Get(request)

  def List(
      self,
      location_resource: resources.Resource,
      filter_expression: str | None = None,
      page_size: int | None = None,
      order_by: str | None = None,
  ) -> backupdr_v1alpha_messages.ListRestoreTemplatesResponse:
    """Lists RestoreTemplate resources in the specified location.

    Args:
      location_resource: The parsed resource reference for the parent location.
      filter_expression: Optional filter expression to restrict results.
      page_size: Optional maximum number of templates to return per page.
      order_by: Optional sort order specification.

    Returns:
      The ListRestoreTemplatesResponse containing matching templates.
    """
    request = (
        self.messages.BackupdrProjectsLocationsRestoreTemplatesListRequest(
            parent=location_resource.RelativeName(),
            filter=filter_expression,
            pageSize=page_size,
            orderBy=order_by,
        )
    )
    return self.service.List(request)

  def Update(
      self,
      template_resource: resources.Resource,
      template: backupdr_v1alpha_messages.RestoreTemplate,
      update_mask: str | None = None,
  ) -> backupdr_v1alpha_messages.Operation:
    """Updates an existing RestoreTemplate resource.

    Args:
      template_resource: The parsed resource reference for the restore template.
      template: The RestoreTemplate message containing updated field values.
      update_mask: Comma-separated list of field paths to update.

    Returns:
      The long-running Operation message for the update request.
    """
    request_id = command_util.GenerateRequestId()
    request = (
        self.messages.BackupdrProjectsLocationsRestoreTemplatesPatchRequest(
            name=template_resource.RelativeName(),
            restoreTemplate=template,
            updateMask=update_mask,
            requestId=request_id,
        )
    )
    return self.service.Patch(request)

  def Run(
      self,
      template_resource: resources.Resource,
      backup: str | None = None,
  ) -> backupdr_v1alpha_messages.Operation:
    """Runs a RestoreTemplate on-demand.

    Args:
      template_resource: The parsed resource reference for the restore template.
      backup: Optional full resource name of a specific backup to restore from.

    Returns:
      The long-running Operation message for the run request.
    """
    run_req = self.messages.RunRestoreTemplateRequest(backup=backup)
    request = self.messages.BackupdrProjectsLocationsRestoreTemplatesRunRequest(
        name=template_resource.RelativeName(),
        runRestoreTemplateRequest=run_req,
    )
    return self.service.Run(request)

  def Delete(
      self,
      template_resource: resources.Resource,
      force: bool = False,
  ) -> backupdr_v1alpha_messages.Operation:
    """Deletes the specified RestoreTemplate resource.

    Args:
      template_resource: The parsed resource reference for the restore template.
      force: If True, also deletes any child RestoreTemplateExecution resources.

    Returns:
      The long-running Operation message for the delete request.
    """
    request = (
        self.messages.BackupdrProjectsLocationsRestoreTemplatesDeleteRequest(
            name=template_resource.RelativeName(),
            force=force if force else None,
        )
    )
    return self.service.Delete(request)
