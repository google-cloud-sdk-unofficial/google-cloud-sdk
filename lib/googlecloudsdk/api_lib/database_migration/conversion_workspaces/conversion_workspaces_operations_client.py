# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Database Migration Service conversion workspaces operations APIs."""

import os
from typing import Any, Iterable, Mapping, Optional

from googlecloudsdk.api_lib.database_migration.conversion_workspaces import base_conversion_workspaces_client
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import files


class ConversionWorkspacesOperationsClient(
    base_conversion_workspaces_client.BaseConversionWorkspacesClient
):
  """Client for conversion workspaces operations APIs."""

  @property
  def file_format_to_rules_format(self) -> Mapping[str, Any]:
    """Returns the translation between file format and rules format.

    Returns:
      The translation between file format and rules format.
    """
    return {
        'ORA2PG': (
            self.messages.ImportMappingRulesRequest.RulesFormatValueValuesEnum.IMPORT_RULES_FILE_FORMAT_ORATOPG_CONFIG_FILE
        ),
    }

  def Seed(
      self,
      name: str,
      src_connection_profile_ref,
      dest_connection_profile_ref,
      auto_commit: bool,
      gcs_bucket: Optional[str] = None,
      gcs_prefix: Optional[str] = None,
  ):
    """Seeds a conversion workspace from a connection profile or GCS.

    Args:
      name: str, the reference of the conversion workspace to seed.
      src_connection_profile_ref: a Resource reference to a
        datamigration.projects.locations.connectionProfiles resource for source
        connection profile.
      dest_connection_profile_ref: a Resource reference to a
        datamigration.projects.locations.connectionProfiles resource for
        destination connection profile.
      auto_commit: bool, whether to auto commit the conversion workspace.
      gcs_bucket: Optional[str], the Cloud Storage bucket containing the schema
        report files.
      gcs_prefix: Optional[str], the prefix for the report paths in the bucket.

    Returns:
      Operation: the operation for seeding the conversion workspace.
    """
    src_connection_profile = None
    if src_connection_profile_ref is not None:
      src_connection_profile = src_connection_profile_ref.RelativeName()

    # TODO(b/385870529): Remove support for providing a destination connection
    # profile for seed.
    dest_connection_profile = None
    if dest_connection_profile_ref is not None:
      dest_connection_profile = dest_connection_profile_ref.RelativeName()

    gcs_source = None
    if gcs_bucket is not None:
      gcs_source = self.messages.GcsSource(
          bucket=gcs_bucket,
          prefix=gcs_prefix,
      )

    return self.cw_service.Seed(
        self.messages.DatamigrationProjectsLocationsConversionWorkspacesSeedRequest(
            name=name,
            seedConversionWorkspaceRequest=self.messages.SeedConversionWorkspaceRequest(
                sourceConnectionProfile=src_connection_profile,
                destinationConnectionProfile=dest_connection_profile,
                gcsSource=gcs_source,
                autoCommit=auto_commit,
            ),
        ),
    )

  def ImportRules(
      self,
      name: str,
      config_files: Iterable[str],
      file_format: str,
      auto_commit: bool,
  ):
    """Import rules in a conversion workspace.

    Args:
      name: str, the reference of the conversion workspace to import rules in.
      config_files: Iterable[str], the config files to import rules from.
      file_format: str, the file format of the config files.
      auto_commit: bool, whether to auto commit the conversion workspace.

    Returns:
      Operation: the operation for importing rules in the conversion workspace.
    """
    return self.mapping_rules_service.Import(
        self.messages.DatamigrationProjectsLocationsConversionWorkspacesMappingRulesImportRequest(
            parent=name,
            importMappingRulesRequest=self.messages.ImportMappingRulesRequest(
                rulesFiles=self._GetRulesFiles(config_files=config_files),
                rulesFormat=self._GetRulesFormat(file_format=file_format),
                autoCommit=auto_commit,
            ),
        ),
    )

  def Convert(
      self,
      name: str,
      filter_expr: Optional[str],
      auto_commit: bool,
  ):
    """Converts the source entities to draft entities in a conversion workspace.

    Args:
      name: str, the reference of the conversion workspace to seed.
      filter_expr: str, the filter expression to apply to the conversion
        workspace.
      auto_commit: bool, whether to auto commit the conversion workspace.

    Returns:
      Operation: the operation for converting the conversion workspace.
    """
    return self.cw_service.Convert(
        self.messages.DatamigrationProjectsLocationsConversionWorkspacesConvertRequest(
            name=name,
            convertConversionWorkspaceRequest=self.messages.ConvertConversionWorkspaceRequest(
                filter=self.CombineFilters(
                    filter_expr,
                    self.parent_client.crud.GetGlobalFilter(name=name),
                ),
                autoCommit=auto_commit,
            ),
        ),
    )

  def Commit(self, name: str, commit_name: str):
    """Commits a conversion workspace.

    Args:
      name: str, the reference of the conversion workspace to commit.
      commit_name: str, the name of the commit to create.

    Returns:
      Operation: the operation for committing the conversion workspace.
    """
    return self.cw_service.Commit(
        self.messages.DatamigrationProjectsLocationsConversionWorkspacesCommitRequest(
            commitConversionWorkspaceRequest=self.messages.CommitConversionWorkspaceRequest(
                commitName=commit_name,
            ),
            name=name,
        ),
    )

  def Rollback(self, name: str):
    """Rollbacks a conversion workspace.

    Args:
      name: str, the reference of the conversion workspace to rollback.

    Returns:
      Operation: the operation for rollbacking the conversion workspace.
    """
    return self.cw_service.Rollback(
        self.messages.DatamigrationProjectsLocationsConversionWorkspacesRollbackRequest(
            name=name,
            rollbackConversionWorkspaceRequest=self.messages.RollbackConversionWorkspaceRequest(),
        ),
    )

  def Apply(
      self,
      name: str,
      destination_connection_profile_ref,
      filter_expr: Optional[str],
      dry_run: bool = False,
  ):
    """Applies a conversion workspace onto the destination database.

    Args:
      name: str, the reference of the conversion workspace to apply.
      destination_connection_profile_ref: a Resource reference to a
        datamigration.projects.locations.connectionProfiles resource for
        destination connection profile.
      filter_expr: Optional[str], the filter expression to apply to the
        conversion workspace.
      dry_run: bool, whether to only validate the apply process.

    Returns:
      Operation: the operation for applying the conversion workspace.
    """
    return self.cw_service.Apply(
        self.messages.DatamigrationProjectsLocationsConversionWorkspacesApplyRequest(
            name=name,
            applyConversionWorkspaceRequest=self.messages.ApplyConversionWorkspaceRequest(
                connectionProfile=destination_connection_profile_ref.RelativeName(),
                filter=filter_expr,
                dryRun=dry_run,
            ),
        )
    )

  def _GetRulesFiles(self, config_files: Iterable[str]) -> Iterable[Any]:
    """Returns the rules files to import rules from.

    Args:
      config_files: Iterable[str], the config files to import rules from.

    Returns:
      The rules files to import rules from.
    """

    rules_files = []
    for config_file in config_files:
      try:
        rules_files.append(
            self.messages.RulesFile(
                rulesContent=files.ReadFileContents(config_file),
                rulesSourceFilename=os.path.basename(config_file),
            ),
        )
      except files.MissingFileError:
        raise exceptions.BadArgumentException(
            '--config-flies',
            f'specified file [{config_file}] does not exist.',
        )

    return rules_files

  def _GetRulesFormat(self, file_format: str):
    """Returns the file format enum to import rules from.

    Args:
      file_format: str, the file format to import rules from.

    Returns:
      The file format enum to import rules from.
    """
    return self.file_format_to_rules_format.get(
        file_format,
        self.messages.ImportMappingRulesRequest.RulesFormatValueValuesEnum.IMPORT_RULES_FILE_FORMAT_UNSPECIFIED,
    )
