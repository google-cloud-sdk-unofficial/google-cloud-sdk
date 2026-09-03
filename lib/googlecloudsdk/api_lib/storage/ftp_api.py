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
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties

_CREDENTIAL_TYPE_KEY = 'credentialType'
_CREDENTIAL_NAME_KEY = 'credentialName'
_SSH_PUBLIC_KEY_BODY_KEY = 'sshPublicKeyBody'

_DIRECTORY_MAPPING_BUCKET_KEY = 'bucket'
_DIRECTORY_MAPPING_DIRECTORY_KEY = 'directory'
_DIRECTORY_MAPPING_PERMISSION_KEY = 'permission'
_DIRECTORY_MAPPING_BUCKET_PREFIX_KEY = 'bucket_prefix'

NO_UPDATE = object()


class FtpApi:
  """Client wrapper for Cloud FTP API.

  Attributes:
    client: The API client for interacting with the FTP service.
    messages: The API messages module for the FTP service.
    servers_service: The service for interacting with Server resources.
    users_service: The service for interacting with User resources.
    operations_service: Service for long-running operations.
  """

  def __init__(self, api_version='v1alpha'):
    """Initializes the instance.

    Args:
      api_version: str, The API version to use.
    """
    self.client = core_apis.GetClientInstance('ftp', api_version)
    self.messages = core_apis.GetMessagesModule('ftp', api_version)
    self.servers_service = self.client.projects_locations_servers
    self.users_service = self.client.projects_locations_servers_users
    self.operations_service = self.client.projects_locations_operations

  # --- Helper Methods ---

  def _GetParentString(self, location):
    """Constructs parent resource string."""
    project = properties.VALUES.core.project.Get(required=True)
    return 'projects/{}/locations/{}'.format(project, location.lower())

  def _GetServerResourceName(self, location, server_id):
    """Constructs server resource name."""
    parent = self._GetParentString(location)
    return '{}/servers/{}'.format(parent, server_id)

  def _GetUserResourceName(self, location, server_id, user_id):
    """Constructs user resource name."""
    server_name = self._GetServerResourceName(location, server_id)
    return '{}/users/{}'.format(server_name, user_id)

  def _GetServerUpdateMask(
      self,
      display_name=NO_UPDATE,
      allowed_cidr_blocks=NO_UPDATE,
      consumer_accept_list=NO_UPDATE,
      consumer_reject_list=NO_UPDATE,
  ):
    """Constructs update mask for Server resource."""
    update_mask = []
    if display_name is not NO_UPDATE:
      update_mask.append('displayName')
    if allowed_cidr_blocks is not NO_UPDATE:
      update_mask.append('externalConfig.allowedCidrBlocks')
    if consumer_accept_list is not NO_UPDATE:
      update_mask.append('internalConfig.consumerAcceptList')
    if consumer_reject_list is not NO_UPDATE:
      update_mask.append('internalConfig.consumerRejectList')
    return update_mask

  def _GetUserUpdateMask(
      self,
      customer_service_account=NO_UPDATE,
      user_credentials=NO_UPDATE,
      storage_directory_mappings=NO_UPDATE,
  ):
    """Constructs update mask for User resource."""
    update_mask = []
    if customer_service_account is not NO_UPDATE:
      update_mask.append('customerServiceAccount')
    if user_credentials is not NO_UPDATE:
      update_mask.append('userCredentials')
    if storage_directory_mappings is not NO_UPDATE:
      update_mask.append('storageDirectoryMappings')
    return update_mask

  # --- Server Methods ---

  def CreateServer(
      self,
      location,
      server_id,
      display_name=None,
      access_type=None,
      allowed_cidr_blocks=None,
      consumer_accept_list=None,
      consumer_reject_list=None,
      labels=None,
  ):
    """Calls create server API.

    Args:
      location: str, The location to create the server in.
      server_id: str, The ID to use for the server.
      display_name: str, The display name of the server.
      access_type: str, The access type ('EXTERNAL' or 'INTERNAL').
      allowed_cidr_blocks: list[str], Allowed CIDR blocks (for EXTERNAL).
      consumer_accept_list: dict[str, int], Map of project ID to connection
        limit (for INTERNAL).
      consumer_reject_list: list[str], List of project IDs to deny (for
        INTERNAL).
      labels: messages.Server.LabelsValue, Labels to apply to the server.

    Returns:
      messages.Operation, The long-running operation.
    """
    access_enum = self.messages.Server.AccessTypeValueValuesEnum
    if access_type is not None:
      access_type_enum = getattr(access_enum, access_type.upper())
    else:
      access_type_enum = None
    if labels:
      labels_val = self.messages.Server.LabelsValue(
          additionalProperties=[
              self.messages.Server.LabelsValue.AdditionalProperty(
                  key=key, value=value
              )
              for key, value in sorted(labels.items())
          ]
      )
    else:
      labels_val = None

    server_msg = self.messages.Server(
        displayName=display_name,
        accessType=access_type_enum,
        labels=labels_val,
    )

    if access_type_enum == access_enum.EXTERNAL:
      server_msg.externalConfig = self.messages.ExternalServerConfig(
          allowedCidrBlocks=allowed_cidr_blocks
      )
    elif access_type_enum == access_enum.INTERNAL:
      accept_list = self._ParseConsumerAcceptList(consumer_accept_list)
      reject_list = self._ParseConsumerRejectList(consumer_reject_list)
      server_msg.internalConfig = self.messages.InternalServerConfig(
          consumerAcceptList=accept_list,
          consumerRejectList=reject_list,
      )

    parent = self._GetParentString(location)
    req = self.messages.FtpProjectsLocationsServersCreateRequest(
        parent=parent,
        serverId=server_id,
        server=server_msg,
    )
    return self.servers_service.Create(req)

  def GetServer(self, location, server_id):
    """Calls get server API.

    Args:
      location: str, The location of the server.
      server_id: str, The ID of the server.

    Returns:
      messages.Server, The server resource.
    """
    name = self._GetServerResourceName(location, server_id)
    req = self.messages.FtpProjectsLocationsServersGetRequest(name=name)
    return self.servers_service.Get(req)

  def UpdateServer(
      self,
      location,
      server_id,
      display_name=NO_UPDATE,
      allowed_cidr_blocks=NO_UPDATE,
      consumer_accept_list=NO_UPDATE,
      consumer_reject_list=NO_UPDATE,
      existing_server=None,
  ):
    """Calls patch server API.

    Args:
      location: str, The location of the server.
      server_id: str, The ID of the server.
      display_name: str, The new display name (if updating).
      allowed_cidr_blocks: list[str], The new allowed CIDR blocks (if updating).
      consumer_accept_list: dict[str, int], The new consumer accept list (if
        updating).
      consumer_reject_list: list[str], The new consumer reject list (if
        updating).
      existing_server: messages.Server, The existing server resource (required
        to verify access type and build update mask). If not provided, it will
        be fetched.

    Returns:
      messages.Operation, The long-running operation.
    """
    name = self._GetServerResourceName(location, server_id)
    if not existing_server:
      existing_server = self.GetServer(location, server_id)

    server_msg = self.messages.Server(name=name)
    update_mask = self._GetServerUpdateMask(
        display_name=display_name,
        allowed_cidr_blocks=allowed_cidr_blocks,
        consumer_accept_list=consumer_accept_list,
        consumer_reject_list=consumer_reject_list,
    )

    if display_name is not NO_UPDATE:
      server_msg.displayName = display_name

    if (
        existing_server.accessType
        == self.messages.Server.AccessTypeValueValuesEnum.EXTERNAL
    ):
      if allowed_cidr_blocks is not NO_UPDATE:
        server_msg.externalConfig = self.messages.ExternalServerConfig(
            allowedCidrBlocks=allowed_cidr_blocks
        )
    elif (
        existing_server.accessType
        == self.messages.Server.AccessTypeValueValuesEnum.INTERNAL
    ):
      internal_config = self.messages.InternalServerConfig()
      modified = False
      if consumer_accept_list is not NO_UPDATE:
        internal_config.consumerAcceptList = self._ParseConsumerAcceptList(
            consumer_accept_list
        )
        modified = True
      if consumer_reject_list is not NO_UPDATE:
        internal_config.consumerRejectList = self._ParseConsumerRejectList(
            consumer_reject_list
        )
        modified = True
      if modified:
        server_msg.internalConfig = internal_config

    if not update_mask:
      raise ValueError(
          f'No fields specified to update for server [{server_id}].'
      )

    req = self.messages.FtpProjectsLocationsServersPatchRequest(
        name=name,
        server=server_msg,
        updateMask=','.join(update_mask),
    )
    return self.servers_service.Patch(req)

  def DeleteServer(self, location, server_id):
    """Calls delete server API.

    Args:
      location: str, The location of the server.
      server_id: str, The ID of the server to delete.

    Returns:
      messages.Operation, The long-running operation.
    """
    name = self._GetServerResourceName(location, server_id)
    req = self.messages.FtpProjectsLocationsServersDeleteRequest(name=name)
    return self.servers_service.Delete(req)

  def ListServers(self, location, page_size=None, limit=None):
    """Calls list servers API.

    Args:
      location: str, The location to list servers for.
      page_size: int, The maximum number of servers to return per page.
      limit: int, The maximum number of servers to return in total.

    Returns:
      Generator[messages.Server], A generator of server resources.
    """
    parent = self._GetParentString(location)
    req = self.messages.FtpProjectsLocationsServersListRequest(parent=parent)
    return list_pager.YieldFromList(
        self.servers_service,
        req,
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
        field='servers',
    )

  def StartServer(self, location, server_id):
    """Calls start server API.

    Args:
      location: str, The location of the server.
      server_id: str, The ID of the server.

    Returns:
      messages.Operation, The long-running operation.
    """
    name = self._GetServerResourceName(location, server_id)
    req = self.messages.FtpProjectsLocationsServersStartRequest(name=name)
    return self.servers_service.Start(req)

  def StopServer(self, location, server_id):
    """Calls stop server API.

    Args:
      location: str, The location of the server.
      server_id: str, The ID of the server.

    Returns:
      messages.Operation, The long-running operation.
    """
    name = self._GetServerResourceName(location, server_id)
    req = self.messages.FtpProjectsLocationsServersStopRequest(name=name)
    return self.servers_service.Stop(req)

  def _ParseConsumerAcceptList(self, accept_dict):
    """Parses consumer-accept-list dict into AllowedConsumer messages.

    Args:
      accept_dict: dict[str, int], Map of project ID to connection limit.

    Returns:
      list[messages.AllowedConsumer] or None.
    """
    if not accept_dict:
      return []
    consumer_list = []
    for project, limit in accept_dict.items():
      if not project.startswith('projects/'):
        project = 'projects/{}'.format(project)
      consumer_list.append(
          self.messages.AllowedConsumer(
              project=project, connectionLimit=int(limit)
          )
      )
    return consumer_list

  def _ParseConsumerRejectList(self, reject_list):
    """Parses consumer-reject-list into DeniedConsumer messages.

    Args:
      reject_list: list[str], List of project IDs.

    Returns:
      list[messages.DeniedConsumer] or None.
    """
    if not reject_list:
      return []
    consumer_list = []
    for project in reject_list:
      if not project.startswith('projects/'):
        project = 'projects/{}'.format(project)
      consumer_list.append(self.messages.DeniedConsumer(project=project))
    return consumer_list

  # --- User Methods ---

  def CreateUser(
      self,
      location,
      server_id,
      user_id,
      customer_service_account=None,
      user_credentials=None,
      storage_directory_mappings=None,
  ):
    """Calls create user API.

    Args:
      location: str, The location of the parent server.
      server_id: str, The ID of the parent server.
      user_id: str, The ID to use for the user.
      customer_service_account: str, The customer service account.
      user_credentials: list[dict], List of credentials.
      storage_directory_mappings: list[dict], List of directory mappings.

    Returns:
      messages.Operation, The long-running operation.
    """
    creds = self._ParseUserCredentials(user_credentials)
    mappings = self._ParseStorageDirectoryMappings(storage_directory_mappings)

    user_msg = self.messages.User(
        customerServiceAccount=customer_service_account,
        userCredentials=creds or [],
        storageDirectoryMappings=mappings or [],
    )

    parent = self._GetServerResourceName(location, server_id)
    req = self.messages.FtpProjectsLocationsServersUsersCreateRequest(
        parent=parent,
        userId=user_id,
        user=user_msg,
    )
    return self.users_service.Create(req)

  def GetUser(self, location, server_id, user_id):
    """Calls get user API.

    Args:
      location: str, The location of the server.
      server_id: str, The ID of the server.
      user_id: str, The ID of the user.

    Returns:
      messages.User, The user resource.
    """
    name = self._GetUserResourceName(location, server_id, user_id)
    req = self.messages.FtpProjectsLocationsServersUsersGetRequest(name=name)
    return self.users_service.Get(req)

  def UpdateUser(
      self,
      location,
      server_id,
      user_id,
      customer_service_account=NO_UPDATE,
      user_credentials=NO_UPDATE,
      storage_directory_mappings=NO_UPDATE,
  ):
    """Calls patch user API.

    Args:
      location: str, The location of the server.
      server_id: str, The ID of the server.
      user_id: str, The ID of the user.
      customer_service_account: str, The new customer service account.
      user_credentials: list[dict], The new user credentials.
      storage_directory_mappings: list[dict], The new storage directory
        mappings.

    Returns:
      messages.Operation, The long-running operation.
    """
    name = self._GetUserResourceName(location, server_id, user_id)
    user_msg = self.messages.User(name=name)
    update_mask = self._GetUserUpdateMask(
        customer_service_account=customer_service_account,
        user_credentials=user_credentials,
        storage_directory_mappings=storage_directory_mappings,
    )

    if customer_service_account is not NO_UPDATE:
      user_msg.customerServiceAccount = customer_service_account

    if user_credentials is not NO_UPDATE:
      user_msg.userCredentials = (
          self._ParseUserCredentials(user_credentials) or []
      )

    if storage_directory_mappings is not NO_UPDATE:
      user_msg.storageDirectoryMappings = (
          self._ParseStorageDirectoryMappings(storage_directory_mappings) or []
      )

    if not update_mask:
      raise ValueError(f'No fields specified to update for user [{user_id}].')

    req = self.messages.FtpProjectsLocationsServersUsersPatchRequest(
        name=name,
        user=user_msg,
        updateMask=','.join(update_mask),
    )
    return self.users_service.Patch(req)

  def DeleteUser(self, location, server_id, user_id, force=False):
    """Calls delete user API.

    Args:
      location: str, The location of the server.
      server_id: str, The ID of the server.
      user_id: str, The ID of the user to delete.
      force: bool, Whether to force deletion.

    Returns:
      messages.Operation, The long-running operation.
    """
    name = self._GetUserResourceName(location, server_id, user_id)
    req = self.messages.FtpProjectsLocationsServersUsersDeleteRequest(
        name=name, force=force
    )
    return self.users_service.Delete(req)

  def ListUsers(self, location, server_id, page_size=None, limit=None):
    """Calls list users API.

    Args:
      location: str, The location of the parent server.
      server_id: str, The ID of the parent server.
      page_size: int, The maximum number of users to return per page.
      limit: int, The maximum number of users to return in total.

    Returns:
      Generator[messages.User], A generator of user resources.
    """
    parent = self._GetServerResourceName(location, server_id)
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

  def _ParseUserCredentials(self, creds_list):
    """Parses JSON-like dict list into UserCredential messages.

    Args:
      creds_list: list[dict], List of credentials.

    Returns:
      list[messages.UserCredential] or None.
    """
    if not creds_list:
      return None
    res = []
    for cred in creds_list:
      try:
        type_enum = getattr(
            self.messages.UserCredential.CredentialTypeValueValuesEnum,
            cred[_CREDENTIAL_TYPE_KEY].upper(),
        )
      except AttributeError as exc:
        valid_types = [
            e.name
            for e in self.messages.UserCredential.CredentialTypeValueValuesEnum
            if e.name != 'TYPE_UNSPECIFIED'
        ]
        raise exceptions.Error(
            'Unsupported credential type: [{}]. Valid choices are: [{}]'.format(
                cred[_CREDENTIAL_TYPE_KEY], ', '.join(valid_types)
            )
        ) from exc
      msg = self.messages.UserCredential(
          credentialName=cred[_CREDENTIAL_NAME_KEY],
          credentialType=type_enum,
      )
      if _SSH_PUBLIC_KEY_BODY_KEY in cred:
        msg.sshPublicKeyBody = cred[_SSH_PUBLIC_KEY_BODY_KEY]
      res.append(msg)
    return res

  def _ParseStorageDirectoryMappings(self, mapping_list):
    """Parses repeated dicts into StorageDirectoryMapping messages.

    Args:
      mapping_list: list[dict], List of directory mappings.

    Returns:
      list[messages.StorageDirectoryMapping] or None.
    """
    if not mapping_list:
      return None
    res = []
    for mapping in mapping_list:
      if _DIRECTORY_MAPPING_PERMISSION_KEY not in mapping:
        raise ValueError(
            'Each storage directory mapping must include a "permission" key.'
        )
      perm_enum = getattr(
          self.messages.StorageDirectoryMapping.PermissionValueValuesEnum,
          mapping[_DIRECTORY_MAPPING_PERMISSION_KEY].upper(),
      )
      msg = self.messages.StorageDirectoryMapping(
          bucket=mapping[_DIRECTORY_MAPPING_BUCKET_KEY],
          directory=mapping[_DIRECTORY_MAPPING_DIRECTORY_KEY],
          permission=perm_enum,
      )
      if _DIRECTORY_MAPPING_BUCKET_PREFIX_KEY in mapping:
        msg.bucketPrefix = mapping[_DIRECTORY_MAPPING_BUCKET_PREFIX_KEY]
      res.append(msg)
    return res

  # --- Operation Methods ---

  def WaitForOperation(
      self, operation_ref, message, result_service=None, max_wait_ms=3600000
  ):
    """Waits for a long-running operation to complete.

    Args:
      operation_ref: resources.Resource, The operation resource reference.
      message: str, The message to display to the user while waiting.
      result_service: apitools.base.py.base_api.BaseApiService, The service for
        retrieving the resulting resource. If None, assumes operation creates no
        resource (e.g. Delete).
      max_wait_ms: int, The maximum wait time in milliseconds.

    Returns:
      messages.Operation or None, The resulting resource or None.
    """
    if result_service:
      poller = waiter.CloudOperationPoller(
          result_service, self.operations_service
      )
    else:
      poller = waiter.CloudOperationPollerNoResources(self.operations_service)

    return waiter.WaitFor(
        poller, operation_ref, message, max_wait_ms=max_wait_ms
    )
