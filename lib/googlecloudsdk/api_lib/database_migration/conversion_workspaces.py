# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Database Migration Service conversion workspaces API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.resource import resource_property


class UnsupportedConversionWorkspaceDBTypeError(core_exceptions.Error):
  """Error raised when the conversion workspace database type is unsupported."""


class ConversionWorkspacesClient(object):
  """Client for connection profiles service in the API."""

  _FIELDS_MAP = ['display_name']

  def __init__(self, release_track):
    self._api_version = api_util.GetApiVersion(release_track)
    self.client = api_util.GetClientInstance(release_track)
    self.messages = api_util.GetMessagesModule(release_track)
    self._service = self.client.projects_locations_conversionWorkspaces
    self._release_track = release_track

  def _GetDatabaseEngine(self, database_engine):
    return self.messages.DatabaseEngineInfo.EngineValueValuesEnum.lookup_by_name(
        database_engine)

  def _GetDatabaseEngineInfo(self, database_engine, database_version):
    return self.messages.DatabaseEngineInfo(
        engine=self._GetDatabaseEngine(database_engine),
        version=database_version)

  def _GetConversionWorkspace(self, args):
    """Returns a conversion workspace."""
    conversion_workspace_type = self.messages.ConversionWorkspace
    global_settings = labels_util.ParseCreateArgs(
        args, conversion_workspace_type.GlobalSettingsValue, 'global_settings')
    source = self._GetDatabaseEngineInfo(args.source_database_engine,
                                         args.source_database_version)
    destination = self._GetDatabaseEngineInfo(args.destination_database_engine,
                                              args.destination_database_version)
    return conversion_workspace_type(
        globalSettings=global_settings,
        displayName=args.display_name,
        source=source,
        destination=destination)

  def _GetUpdateMask(self, args):
    """Returns update mask for specified fields."""
    update_fields = [
        resource_property.ConvertToCamelCase(field)
        for field in sorted(self._FIELDS_MAP)
        if args.IsSpecified(field)
    ]
    return update_fields

  def _GetUpdatedConversionWorkspace(self, conversion_workspace, args):
    """Returns updated conversion workspace and list of updated fields."""
    update_fields = self._GetUpdateMask(args)
    if args.IsSpecified('display_name'):
      conversion_workspace.displayName = args.display_name
    return conversion_workspace, update_fields

  def _GetExistingConversionWorkspace(self, name):
    get_req = self.messages.DatamigrationProjectsLocationsConversionWorkspacesGetRequest(
        name=name)
    return self._service.Get(get_req)

  def _GetCommitConversionWorkspaceRequest(self, args):
    """Returns commit conversion workspace request."""
    return self.messages.CommitConversionWorkspaceRequest(
        commitName=args.commit_name)

  def Create(self, parent_ref, conversion_workspace_id, args=None):
    """Creates a conversion workspace.

    Args:
      parent_ref: a Resource reference to a parent
        datamigration.projects.locations resource for this conversion workspace.
      conversion_workspace_id: str, the name of the resource to create.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Operation: the operation for creating the conversion workspace.
    """
    conversion_workspace = self._GetConversionWorkspace(args)

    request_id = api_util.GenerateRequestId()
    create_req_type = self.messages.DatamigrationProjectsLocationsConversionWorkspacesCreateRequest
    create_req = create_req_type(
        conversionWorkspace=conversion_workspace,
        conversionWorkspaceId=conversion_workspace_id,
        parent=parent_ref,
        requestId=request_id)

    return self._service.Create(create_req)

  def Update(self, name, args=None):
    """Updates a conversion workspace.

    Args:
      name: str, the reference of the conversion workspace to update.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Operation: the operation for updating the conversion workspace
    """
    current_cw = self._GetExistingConversionWorkspace(name)

    conversion_workspace, update_fields = self._GetUpdatedConversionWorkspace(
        current_cw, args)

    request_id = api_util.GenerateRequestId()
    update_req_type = self.messages.DatamigrationProjectsLocationsConversionWorkspacesPatchRequest
    update_req = update_req_type(
        conversionWorkspace=conversion_workspace,
        name=name,
        requestId=request_id,
        updateMask=','.join(update_fields))

    return self._service.Patch(update_req)

  def Commit(self, name, args=None):
    """Commits a conversion workspace.

    Args:
      name: str, the reference of the conversion workspace to commit.
      args: argparse.Namespace, the arguments that this command was invoked
        with.

    Returns:
      Operation: the operation for committing the conversion workspace
    """
    commit_req_type = self.messages.DatamigrationProjectsLocationsConversionWorkspacesCommitRequest
    commit_req = commit_req_type(
        commitConversionWorkspaceRequest=self
        ._GetCommitConversionWorkspaceRequest(args),
        name=name)

    return self._service.Commit(commit_req)

  def Rollback(self, name):
    """Rollbacks a conversion workspace.

    Args:
      name: str, the reference of the conversion workspace to rollback.

    Returns:
      Operation: the operation for rollbacking the conversion workspace
    """
    rollback_req_type = self.messages.DatamigrationProjectsLocationsConversionWorkspacesRollbackRequest
    rollback_req = rollback_req_type(
        name=name,
        rollbackConversionWorkspaceRequest=self.messages
        .RollbackConversionWorkspaceRequest())

    return self._service.Rollback(rollback_req)