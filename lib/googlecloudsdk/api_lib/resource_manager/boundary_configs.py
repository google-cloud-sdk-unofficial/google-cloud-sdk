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
"""CRM API BoundaryConfigs utilities."""

from typing import Any

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources

API_VERSION = 'v3'


def BoundaryConfigsClient(api_version: str = API_VERSION) -> Any:
  """Returns a client instance of the CRM BoundaryConfigs service."""
  return apis.GetClientInstance('cloudresourcemanager', api_version)


def BoundaryConfigsMessages(api_version: str = API_VERSION) -> Any:
  """Returns the messages module for the BoundaryConfigs service."""
  return apis.GetMessagesModule('cloudresourcemanager', api_version)


class BoundaryConfigOperationPoller(waiter.OperationPoller):
  """Poller for long running operations on BoundaryConfigs."""

  def __init__(self, operations_service: Any) -> None:
    """Initializes the OperationPoller.

    Args:
      operations_service: The Cloud Resource Manager operations service.
    """
    self.operations_service = operations_service

  def IsDone(self, operation: Any) -> bool:
    if operation.done:
      if operation.error:
        raise waiter.OperationError(operation.error.message)
      return True
    return False

  def Poll(self, operation_ref: Any) -> Any:
    request_type = self.operations_service.GetRequestType('Get')
    return self.operations_service.Get(
        request_type(name=operation_ref.RelativeName())
    )

  def GetResult(self, operation: Any) -> Any:
    messages = BoundaryConfigsMessages()
    return encoding.PyValueToMessage(
        messages.BoundaryConfig,
        encoding.MessageToPyValue(operation.response),
    )


def WaitForOperation(
    operation: Any,
    message: str = 'Waiting for operation to finish',
    max_wait_sec: int = 60,
) -> Any:
  """Waits for an Operation to complete using waiter.WaitFor."""
  client = BoundaryConfigsClient()
  poller = BoundaryConfigOperationPoller(client.operations)
  if operation.done:
    if operation.error:
      raise waiter.OperationError(operation.error.message)
    return poller.GetResult(operation)
  operation_ref = resources.REGISTRY.Parse(
      operation.name,
      collection='cloudresourcemanager.operations',
      api_version=API_VERSION,
  )
  return waiter.WaitFor(
      poller,
      operation_ref,
      message,
      max_wait_ms=max_wait_sec * 1000,
  )


def GetBoundaryConfig(name: str, api_version: str = API_VERSION) -> Any:
  """Gets a BoundaryConfig by resource name."""
  client = BoundaryConfigsClient(api_version)
  messages = BoundaryConfigsMessages(api_version)
  if name.startswith('organizations/'):
    request = (
        messages.CloudresourcemanagerOrganizationsGetBoundaryConfigRequest(
            name=name
        )
    )
    return client.organizations.GetBoundaryConfig(request)
  request = messages.CloudresourcemanagerFoldersGetBoundaryConfigRequest(
      name=name
  )
  return client.folders.GetBoundaryConfig(request)


def UpdateBoundaryConfig(
    name: str,
    tag_key: str,
    etag: str | None = None,
    api_version: str = API_VERSION,
) -> Any:
  """Updates a BoundaryConfig."""
  client = BoundaryConfigsClient(api_version)
  messages = BoundaryConfigsMessages(api_version)
  boundary_config = messages.BoundaryConfig(tagKey=tag_key)
  if etag is not None:
    boundary_config.etag = etag

  if name.startswith('organizations/'):
    request = (
        messages.CloudresourcemanagerOrganizationsUpdateBoundaryConfigRequest(
            name=name,
            boundaryConfig=boundary_config,
            updateMask='tagKey',
        )
    )
    return client.organizations.UpdateBoundaryConfig(request)

  request = messages.CloudresourcemanagerFoldersUpdateBoundaryConfigRequest(
      name=name,
      boundaryConfig=boundary_config,
      updateMask='tagKey',
  )
  return client.folders.UpdateBoundaryConfig(request)
