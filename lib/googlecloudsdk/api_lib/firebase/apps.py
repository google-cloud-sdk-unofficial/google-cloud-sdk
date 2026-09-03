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
"""API client helper for Firebase Apps management."""

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.firebase import exceptions as firebase_exceptions
from googlecloudsdk.api_lib.firebase import util as firebase_util
from googlecloudsdk.api_lib.util import waiter

VALID_PLATFORMS = ('android', 'ios', 'web')


class FirebaseAppsOperationPoller(waiter.OperationPoller):
  """Poller for Firebase long running operations."""

  def __init__(self, client, messages):
    self.client = client
    self.messages = messages

  def IsDone(self, operation):
    return operation.done

  def Poll(self, operation_ref):
    request = self.messages.FirebaseOperationsGetRequest(name=operation_ref)
    return self.client.operations.Get(request)

  def GetResult(self, operation):
    if operation.error:
      raise firebase_exceptions.FirebaseError(
          f'Operation failed: {operation.error.message}'
      )
    if operation.response:
      return encoding.MessageToPyValue(operation.response)
    return {}


def _FormatApp(app, platform):
  """Formats an app message into a dictionary for display."""
  return {
      'displayName': app.displayName,
      'appId': app.appId,
      'platform': platform.upper(),
      'namespace': getattr(app, 'bundleId', None) or getattr(app, 'packageName', None),
      'appStoreId': getattr(app, 'appStoreId', None),
      'urls': ', '.join(app.appUrls) if getattr(app, 'appUrls', None) else None,
  }


class AppsClient:
  """Client for Firebase Apps management API."""

  def __init__(self, client=None, messages=None):
    """Initializes the Firebase Apps management API client.

    Args:
      client: base_api.BaseApiClient, Optional Apitools client instance. If not
        provided, a client instance for the default API version is used.
      messages: module, Optional Apitools messages module. If not provided,
        messages module for the default API version is used.
    """
    self.client = client or firebase_util.GetClientInstance(
        api_version='v1beta1'
    )
    self.messages = messages or firebase_util.GetMessagesModule(
        api_version='v1beta1'
    )

  def ListApps(self, project_id, platform=None):
    """List registered Firebase apps in a project.

    Args:
      project_id: str, Google Cloud project ID.
      platform: str, Optional platform to filter by ('ios', 'android', 'web').

    Returns:
      list of dicts containing app details.
    """
    parent = firebase_util.GetProjectRef(project_id).RelativeName()
    filter_platform = platform.lower() if platform else None
    listed = []

    platform_handlers = [
        ('ios', self.client.projects_iosApps, self.messages.FirebaseProjectsIosAppsListRequest),
        ('android', self.client.projects_androidApps, self.messages.FirebaseProjectsAndroidAppsListRequest),
        ('web', self.client.projects_webApps, self.messages.FirebaseProjectsWebAppsListRequest),
    ]

    for plat_name, service, request_cls in platform_handlers:
      if filter_platform and filter_platform != plat_name:
        continue
      try:
        req = request_cls(parent=parent)
        res = service.List(req)
        if res.apps:
          listed.extend([_FormatApp(app, plat_name) for app in res.apps])
      except apitools_exceptions.HttpError as e:
        firebase_util.HandleHttpError(e)

    return listed

  def CreateApp(
      self,
      project_id,
      platform,
      display_name=None,
      package_name=None,
      bundle_id=None,
      app_store_id=None,
  ):
    """Create a new Firebase app.

    Args:
      project_id: str, Google Cloud project ID.
      platform: str, Platform ('android', 'ios', 'web').
      display_name: str, Optional display name for the app.
      package_name: str, Package name for Android apps.
      bundle_id: str, Bundle ID for iOS apps.
      app_store_id: str, Optional App Store ID for iOS apps.

    Returns:
      dict with created app details.
    """
    platform_lower = platform.lower()
    if platform_lower not in VALID_PLATFORMS:
      raise firebase_exceptions.InvalidAppTypeError(
          f'Unsupported platform: {platform}'
      )

    parent = firebase_util.GetProjectRef(project_id).RelativeName()

    try:
      if platform_lower == 'android':
        req = self.messages.FirebaseProjectsAndroidAppsCreateRequest(
            parent=parent,
            androidApp=self.messages.AndroidApp(
                displayName=display_name, packageName=package_name
            ),
        )
        op = self.client.projects_androidApps.Create(req)
      elif platform_lower == 'ios':
        req = self.messages.FirebaseProjectsIosAppsCreateRequest(
            parent=parent,
            iosApp=self.messages.IosApp(
                displayName=display_name,
                bundleId=bundle_id,
                appStoreId=app_store_id,
            ),
        )
        op = self.client.projects_iosApps.Create(req)
      elif platform_lower == 'web':
        req = self.messages.FirebaseProjectsWebAppsCreateRequest(
            parent=parent,
            webApp=self.messages.WebApp(displayName=display_name),
        )
        op = self.client.projects_webApps.Create(req)
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

    poller = FirebaseAppsOperationPoller(self.client, self.messages)
    wait_message = (
        f'Waiting for app creation operation [{op.name}] to complete...'
    )
    result = waiter.WaitFor(
        poller, op.name, wait_message, max_wait_ms=300000, sleep_ms=2000
    )
    return result or {}
