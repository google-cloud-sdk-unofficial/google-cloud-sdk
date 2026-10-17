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
"""Secure Source Manager API utilities."""

from apitools.base.protorpclite import messages as protorpc_messages
from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages

DEFAULT_API_NAME = 'securesourcemanager'
DEFAULT_API_VERSION = 'v1'

VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1',
    base.ReleaseTrack.BETA: 'v1',
    base.ReleaseTrack.GA: 'v1',
}


def GetApiVersion(release_track=base.ReleaseTrack.ALPHA):
  return VERSION_MAP.get(release_track, DEFAULT_API_VERSION)


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA, location=None):
  api_version = GetApiVersion(release_track)
  return apis.GetClientInstance(
      DEFAULT_API_NAME, api_version, location=location
  )


def GetMessagesModule(release_track=base.ReleaseTrack.ALPHA):
  api_version = GetApiVersion(release_track)
  return apis.GetMessagesModule(DEFAULT_API_NAME, api_version)


def GetResourceNameFromResponse(
    response: protorpc_messages.Message | None,
) -> str | None:
  """Returns the `name` field of an operation response, if present.

  Args:
    response: The operation response or resource message.

  Returns:
    The resource name, or None if the response is empty or has no name.
  """
  if not response:
    return None
  return encoding.MessageToPyValue(response).get('name')


class SecureSourceManagerClientBase(object):
  """Base class for Secure Source Manager API client wrappers."""

  def __init__(self, release_track=base.ReleaseTrack.ALPHA, location=None):
    api_version = GetApiVersion(release_track)
    self._client = GetClientInstance(release_track, location=location)
    self._messages = self._client.MESSAGES_MODULE
    self._service = None
    self.operations_service = self._client.projects_locations_operations
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName(DEFAULT_API_NAME, api_version)

  @property
  def client(self):
    return self._client

  @property
  def messages(self):
    return self._messages

  def GetOperationRef(
      self, operation: securesourcemanager_v1_messages.Operation
  ) -> resources.Resource | None:
    """Converts an Operation to a Resource that can be used with `waiter.WaitFor`."""
    if operation.name is None:
      return None
    return self._resource_parser.ParseRelativeName(
        operation.name,
        collection='securesourcemanager.projects.locations.operations',
    )

  def WaitForOperation(
      self,
      operation_ref: resources.Resource | None,
      message: str,
      has_result: bool = True,
  ) -> protorpc_messages.Message | None:
    """Waits for an operation to complete.

    Polls the Secure Source Manager Operation service until the operation
    completes or fails.

    Args:
      operation_ref: A Resource created by GetOperationRef describing the
        operation.
      message: The message to display to the user while they wait.
      has_result: If True, the function will return the target of the operation
        when it completes. If False, returns operation.response directly without
        calling Get on the resource service (useful for Delete or
        batch/multi-resource operations).

    Returns:
      If has_result = True, a Secure Source Manager entity.
      Otherwise, operation.response.
    """
    if has_result:
      poller = waiter.CloudOperationPoller(
          self._service, self.operations_service
      )
    else:
      poller = waiter.CloudOperationPollerNoResources(self.operations_service)

    return waiter.WaitFor(poller, operation_ref, message)

  def GetOperationResult(
      self,
      operation: securesourcemanager_v1_messages.Operation,
      message: str,
      has_result: bool = True,
  ) -> protorpc_messages.Message | None:
    """Returns the result of an operation, waiting for it if needed.

    If the operation is already done (or is not a named long-running
    operation), its response is returned directly. Otherwise, the operation is
    polled until it completes.

    Args:
      operation: The operation returned by a mutating API call.
      message: The message to display to the user while waiting.
      has_result: See `WaitForOperation`.

    Returns:
      The operation response or the resulting Secure Source Manager entity.

    Raises:
      waiter.OperationError: If the operation completed with an error.
    """
    # TODO(b/413742800): Remove the non wait logic once the LRO implemented.
    if operation.done or not operation.name:
      if operation.error:
        log.error('Operation failed: %s', operation.error)
        raise waiter.OperationError(
            operation.error.message or str(operation.error)
        )
      return operation.response

    return self.WaitForOperation(
        self.GetOperationRef(operation), message, has_result=has_result
    )
