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
"""Utilities for the GCP Device Cloud (device-run) API."""

from typing import Any

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker


class UnsupportedReleaseTrackError(Exception):
  """Raised when requesting API version for an unsupported release track."""


def ReleaseTrackToApiVersion(release_track):
  if release_track in (base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA):
    return 'v1alpha'
  else:
    raise UnsupportedReleaseTrackError(release_track)


class DeviceRunClient(object):
  """Base client wrapper for Device Run API."""

  def __init__(self, api_version='v1alpha'):
    self.client = apis.GetClientInstance('devicerun', api_version)
    self.messages = self.client.MESSAGES_MODULE
    self._service = None

  @property
  def service(self):
    return self._service


class SessionsClient(DeviceRunClient):
  """Client for the Sessions service under Device Run API."""

  def __init__(self, api_version='v1alpha'):
    super(SessionsClient, self).__init__(api_version)
    self._service = self.client.projects_locations_sessions

  def Get(self, session_ref):
    """Gets an automation session of Device Run."""
    request = self.messages.DevicerunProjectsLocationsSessionsGetRequest(
        name=session_ref.RelativeName()
    )
    return self._service.Get(request)

  def List(
      self,
      parent_ref,
      limit=None,
      page_size=100,
      filter_str=None,
      order_by=None,
      view=None,
  ):
    """Lists automation sessions of Device Run."""
    request = self.messages.DevicerunProjectsLocationsSessionsListRequest(
        parent=parent_ref.RelativeName(),
        filter=filter_str,
        orderBy=order_by,
        view=view,
    )
    return list_pager.YieldFromList(
        self._service,
        request,
        batch_size=page_size,
        limit=limit,
        field='sessions',
        batch_size_attribute='pageSize',
    )

  def Create(self, parent_ref, session_id=None, request_id=None, session=None):
    """Creates an automation session of Device Run."""
    request = self.messages.DevicerunProjectsLocationsSessionsCreateRequest(
        parent=parent_ref.RelativeName(),
        requestId=request_id,
        sessionId=session_id,
        session=session,
    )
    return self._service.Create(request)

  def Delete(self, session_ref, request_id=None):
    """Deletes an automation session of Device Run."""
    request = self.messages.DevicerunProjectsLocationsSessionsDeleteRequest(
        name=session_ref.RelativeName(),
        requestId=request_id,
    )
    return self._service.Delete(request)

  def Cancel(self, session_ref):
    """Starts asynchronous cancellation on an automation session of Device Run."""
    request = self.messages.DevicerunProjectsLocationsSessionsCancelRequest(
        name=session_ref.RelativeName()
    )
    return self._service.Cancel(request)


class OperationsClient(DeviceRunClient):
  """Client for the Operations service under Device Run API."""

  def __init__(self, api_version='v1alpha'):
    super(OperationsClient, self).__init__(api_version)
    self._service = self.client.projects_locations_operations

  def Get(self, operation_ref):
    """Gets a resource operation of Device Run."""
    request = self.messages.DevicerunProjectsLocationsOperationsGetRequest(
        name=operation_ref.RelativeName()
    )
    return self._service.Get(request)

  def List(self, parent_ref, limit=None, page_size=100, filter_str=None):
    """Lists resource operations of Device Run."""
    request = self.messages.DevicerunProjectsLocationsOperationsListRequest(
        name=parent_ref.RelativeName(),
        filter=filter_str,
    )
    return list_pager.YieldFromList(
        self._service,
        request,
        batch_size=page_size,
        limit=limit,
        field='operations',
        batch_size_attribute='pageSize',
    )

  def Cancel(self, operation_ref):
    """Starts asynchronous cancellation on a long-running operation."""
    request = self.messages.DevicerunProjectsLocationsOperationsCancelRequest(
        name=operation_ref.RelativeName()
    )
    return self._service.Cancel(request)

  def Delete(self, operation_ref):
    """Deletes a long-running operation."""
    request = self.messages.DevicerunProjectsLocationsOperationsDeleteRequest(
        name=operation_ref.RelativeName()
    )
    return self._service.Delete(request)


class LocationsClient(DeviceRunClient):
  """Client for the Locations service under Device Run API."""

  def __init__(self, api_version='v1alpha'):
    super(LocationsClient, self).__init__(api_version)
    self._service = self.client.projects_locations

  def Get(self, location_ref):
    """Gets information about a location."""
    request = self.messages.DevicerunProjectsLocationsGetRequest(
        name=location_ref.RelativeName()
    )
    return self._service.Get(request)

  def List(self, project_ref, limit=None, page_size=100, filter_str=None):
    """Lists information about the supported locations for this service."""
    request = self.messages.DevicerunProjectsLocationsListRequest(
        name=project_ref.RelativeName(),
        filter=filter_str,
    )
    return list_pager.YieldFromList(
        self._service,
        request,
        batch_size=page_size,
        limit=limit,
        field='locations',
        batch_size_attribute='pageSize',
    )


class DevicesClient(DeviceRunClient):
  """Client for the Devices service under Device Run API."""

  def __init__(self, api_version='v1alpha'):
    super(DevicesClient, self).__init__(api_version)
    self._service = self.client.projects_locations_devices

  def Get(self, device_ref):
    """Gets information about a specific device."""
    request = self.messages.DevicerunProjectsLocationsDevicesGetRequest(
        name=device_ref.RelativeName()
    )
    return self._service.Get(request)

  def List(self, location_ref, limit=None, page_size=100):
    """Lists devices."""
    request = self.messages.DevicerunProjectsLocationsDevicesListRequest(
        parent=location_ref.RelativeName(),
    )
    return list_pager.YieldFromList(
        self._service,
        request,
        batch_size=page_size,
        limit=limit,
        field='devices',
        batch_size_attribute='pageSize',
    )


class DeviceRunOperationPoller(waiter.OperationPoller):
  """Implementation of OperationPoller for Device Run LRO Operations."""

  def __init__(self, resource_service, operations_service, resource_ref=None):
    self.resource_service = resource_service
    self.operations_service = operations_service
    self.resource_ref = resource_ref

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
    if self.resource_ref is None:
      return operation
    request_type = self.resource_service.GetRequestType('Get')
    return self.resource_service.Get(
        request_type(name=self.resource_ref.RelativeName())
    )


def WaitForOperation(poller, operation_ref, message):
  """Waits for a Device Run operation to complete, displaying status messages."""
  status_message = ['']

  def _DetailMessageCallback():
    return status_message[0]

  def _TrackerUpdateFunc(unused_tracker, operation, unused_status):
    if getattr(operation, 'metadata', None):
      metadata = encoding.MessageToPyValue(operation.metadata)
      msg = metadata.get('statusMessage')
      if msg:
        status_message[0] = msg

  tracker = progress_tracker.ProgressTracker(
      message,
      detail_message_callback=_DetailMessageCallback,
  )

  return waiter.WaitFor(
      poller,
      operation_ref,
      custom_tracker=tracker,
      tracker_update_func=_TrackerUpdateFunc,
  )


class DeviceRunSessionPoller(waiter.OperationPoller):
  """Implementation of OperationPoller for Device Run Sessions."""

  def __init__(self, sessions_client: SessionsClient):
    self.sessions_client = sessions_client

  def IsDone(self, session: Any) -> bool:
    status_type = (
        str(session.sessionReport.status.statusType)
        if session and session.sessionReport and session.sessionReport.status
        else 'STATUS_TYPE_UNSPECIFIED'
    )
    return status_type == 'DONE'

  def Poll(self, session_ref: resources.Resource) -> Any:
    return self.sessions_client.Get(session_ref)

  def GetResult(self, session: Any) -> Any:
    return session


def WaitForSession(
    poller: DeviceRunSessionPoller,
    session_ref: resources.Resource,
    message: str,
) -> Any:
  """Waits for a Device Run session to complete, displaying progress messages."""
  progress_message = ['']

  def _DetailMessageCallback():
    return progress_message[0]

  def _TrackerUpdateFunc(unused_tracker, session, unused_status):
    if (
        session.sessionReport
        and session.sessionReport.status
        and session.sessionReport.status.progressMessages
    ):
      progress_message[0] = session.sessionReport.status.progressMessages[-1]

  tracker = progress_tracker.ProgressTracker(
      message,
      detail_message_callback=_DetailMessageCallback,
  )

  return waiter.WaitFor(
      poller,
      session_ref,
      custom_tracker=tracker,
      tracker_update_func=_TrackerUpdateFunc,
  )
