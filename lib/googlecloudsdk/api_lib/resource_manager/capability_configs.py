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
"""Utilities for Cloud Resource Manager CapabilityConfigs API."""

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources

API_VERSION = 'v3'


def CapabilityConfigsClient():
  """Returns a client instance of the CRM v3 service."""
  return apis.GetClientInstance('cloudresourcemanager', API_VERSION)


def CapabilityConfigsMessages():
  """Returns the messages module for CRM v3."""
  return apis.GetMessagesModule('cloudresourcemanager', API_VERSION)


def _GetServiceAndRequestPrefix(client, parent_or_name):
  """Returns the appropriate service and request prefix based on resource name/parent."""
  if parent_or_name.startswith('organizations/'):
    return (
        client.organizations_capabilityConfigs,
        'CloudresourcemanagerOrganizationsCapabilityConfigs',
    )
  elif parent_or_name.startswith('folders/'):
    return (
        client.folders_capabilityConfigs,
        'CloudresourcemanagerFoldersCapabilityConfigs',
    )
  elif parent_or_name.startswith('projects/'):
    return (
        client.projects_capabilityConfigs,
        'CloudresourcemanagerProjectsCapabilityConfigs',
    )
  else:
    raise exceptions.Error(
        'Invalid parent or resource name [{}]. Must start with '
        'organizations/, folders/, or projects/.'.format(parent_or_name)
    )


class CapabilityConfigOperationPoller(waiter.OperationPoller):
  """Poller for long running operations on CapabilityConfigs."""

  def __init__(self, operations_service, has_result=True):
    self.operations_service = operations_service
    self.has_result = has_result

  def IsDone(self, operation):
    if operation.done:
      if operation.error:
        raise waiter.OperationError(operation.error.message)
      return True
    return False

  def Poll(self, operation_ref):
    request_type = self.operations_service.GetRequestType('Get')
    return self.operations_service.Get(
        request_type(name=operation_ref.RelativeName())
    )

  def GetResult(self, operation):
    if not self.has_result:
      return None
    if operation.response:
      messages = CapabilityConfigsMessages()
      return encoding.PyValueToMessage(
          messages.CapabilityConfig,
          encoding.MessageToPyValue(operation.response),
      )
    return None


def WaitForOperation(
    operation,
    message='Waiting for operation to finish',
    max_wait_sec=60,
    has_result=True,
):
  """Waits for an Operation to complete using waiter.WaitFor."""
  client = CapabilityConfigsClient()
  poller = CapabilityConfigOperationPoller(
      client.operations, has_result=has_result
  )
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


def Create(parent, capability_config_id, capability_config):
  """Creates a CapabilityConfig under a parent."""
  client = CapabilityConfigsClient()
  messages = CapabilityConfigsMessages()
  service, prefix = _GetServiceAndRequestPrefix(client, parent)
  req_class = getattr(messages, prefix + 'CreateRequest')
  req = req_class(
      parent=parent,
      capabilityConfigId=capability_config_id,
      capabilityConfig=capability_config,
  )
  return service.Create(req)


def Get(name):
  """Retrieves a CapabilityConfig."""
  client = CapabilityConfigsClient()
  messages = CapabilityConfigsMessages()
  service, prefix = _GetServiceAndRequestPrefix(client, name)
  req_class = getattr(messages, prefix + 'GetRequest')
  req = req_class(name=name)
  return service.Get(req)


def List(parent, page_size=None, limit=None):
  """Lists CapabilityConfigs under a parent."""
  client = CapabilityConfigsClient()
  messages = CapabilityConfigsMessages()
  service, prefix = _GetServiceAndRequestPrefix(client, parent)
  req_class = getattr(messages, prefix + 'ListRequest')
  req = req_class(parent=parent)
  return list_pager.YieldFromList(
      service,
      req,
      batch_size=page_size,
      limit=limit,
      field='capabilityConfigs',
      batch_size_attribute='pageSize',
  )


def Update(name, capability_config, update_mask):
  """Updates a CapabilityConfig."""
  client = CapabilityConfigsClient()
  messages = CapabilityConfigsMessages()
  service, prefix = _GetServiceAndRequestPrefix(client, name)
  req_class = getattr(messages, prefix + 'PatchRequest')
  req = req_class(
      name=name,
      capabilityConfig=capability_config,
      updateMask=update_mask,
  )
  return service.Patch(req)


def Delete(name, etag=None):
  """Deletes a CapabilityConfig."""
  client = CapabilityConfigsClient()
  messages = CapabilityConfigsMessages()
  service, prefix = _GetServiceAndRequestPrefix(client, name)
  req_class = getattr(messages, prefix + 'DeleteRequest')
  req_kwargs = {'name': name}
  if etag is not None and hasattr(req_class, 'etag'):
    req_kwargs['etag'] = etag
  req = req_class(**req_kwargs)
  return service.Delete(req)
