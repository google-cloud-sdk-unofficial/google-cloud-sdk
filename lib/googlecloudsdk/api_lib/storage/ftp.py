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
"""Client for interacting with Cloud FTP API."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis as core_apis


class FtpClient(object):
  """Client wrapper for Cloud FTP API.

  Attributes:
    client: The API client for interacting with the FTP service.
    messages: The API messages module for the FTP service.
    servers_service: The service for interacting with Server resources.
    users_service: The service for interacting with User resources.
    operations_service: Service for long-running operations.
  """

  def __init__(self, api_version='v1alpha'):
    """Initializes the instance."""
    self.client = core_apis.GetClientInstance('ftp', api_version)
    self.messages = core_apis.GetMessagesModule('ftp', api_version)
    self.servers_service = self.client.projects_locations_servers
    self.users_service = self.client.projects_locations_servers_users
    self.operations_service = self.client.projects_locations_operations

  # --- Server Methods ---

  def CreateServer(self, parent, server_id, server_msg):
    """Calls create server API."""
    req = self.messages.FtpProjectsLocationsServersCreateRequest(
        parent=parent,
        serverId=server_id,
        server=server_msg,
    )
    return self.servers_service.Create(req)

  def GetServer(self, name):
    """Calls get server API."""
    req = self.messages.FtpProjectsLocationsServersGetRequest(name=name)
    return self.servers_service.Get(req)

  def UpdateServer(self, server_msg, update_mask):
    """Calls patch server API."""
    req = self.messages.FtpProjectsLocationsServersPatchRequest(
        name=server_msg.name,
        server=server_msg,
        updateMask=','.join(update_mask),
    )
    return self.servers_service.Patch(req)

  def DeleteServer(self, name):
    """Calls delete server API."""
    req = self.messages.FtpProjectsLocationsServersDeleteRequest(name=name)
    return self.servers_service.Delete(req)

  def ListServers(self, parent, page_size=None, limit=None):
    """Calls list servers API."""
    req = self.messages.FtpProjectsLocationsServersListRequest(parent=parent)
    return list_pager.YieldFromList(
        self.servers_service,
        req,
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
        field='servers',
    )

  # --- User Methods ---

  def CreateUser(self, parent, user_id, user_msg):
    """Calls create user API."""
    req = self.messages.FtpProjectsLocationsServersUsersCreateRequest(
        parent=parent,
        userId=user_id,
        user=user_msg,
    )
    return self.users_service.Create(req)

  def GetUser(self, name):
    """Calls get user API."""
    req = self.messages.FtpProjectsLocationsServersUsersGetRequest(name=name)
    return self.users_service.Get(req)

  def UpdateUser(self, user_msg, update_mask):
    """Calls patch user API."""
    req = self.messages.FtpProjectsLocationsServersUsersPatchRequest(
        name=user_msg.name,
        user=user_msg,
        updateMask=','.join(update_mask),
    )
    return self.users_service.Patch(req)

  def DeleteUser(self, name, force=False):
    """Calls delete user API."""
    req = self.messages.FtpProjectsLocationsServersUsersDeleteRequest(
        name=name, force=force
    )
    return self.users_service.Delete(req)

  def ListUsers(self, parent, page_size=None, limit=None):
    """Calls list users API."""
    req = self.messages.FtpProjectsLocationsServersUsersListRequest(
        parent=parent
    )
    return list_pager.YieldFromList(
        self.users_service,
        req,
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
        field='users',
    )

  # --- Operation Methods ---

  def GetOperation(self, name):
    """Calls get operation API."""
    req = self.messages.FtpProjectsLocationsOperationsGetRequest(name=name)
    return self.operations_service.Get(req)
