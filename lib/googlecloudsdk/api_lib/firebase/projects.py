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
"""Helper methods for interacting with Firebase Provisioning API."""

from __future__ import annotations

import types
from typing import Any

from apitools.base.py import base_api
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.firebase import util as firebase_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter

_API_NAME = 'firebase'
_API_VERSION = 'v1alpha'
_DEFAULT_APP_NAMESPACE_PREFIX = 'com.example'
_DEFAULT_LOCATION = 'us-west1'
_MAX_WAIT_MS = 300000
_WAIT_POLL_INTERVAL_MS = 2000


def GetClientInstance(no_http=False):
  """Returns a client instance for the Firebase v1alpha API."""
  return apis.GetClientInstance(_API_NAME, _API_VERSION, no_http=no_http)


def GetMessagesModule():
  """Returns the messages module for the Firebase v1alpha API."""
  return apis.GetMessagesModule(_API_NAME, _API_VERSION)


def ProvisionFirebaseApp(
    app_namespace,
    display_name=None,
    parent=None,
    client=None,
):
  """Calls ProvisionFirebaseApp on the Firebase v1alpha API.

  Args:
    app_namespace: str, The web app identifier / app namespace.
    display_name: str, The display name for the new Project and/or Web App.
    parent: str, Parent resource string (e.g. 'projects/my-proj').
    client: apitools client instance, optional.

  Returns:
    Operation message from the API.
  """
  client = client or GetClientInstance()
  messages = GetMessagesModule()

  effective_display_name = display_name or app_namespace

  request = messages.ProvisionFirebaseAppRequest(
      appNamespace=app_namespace,
      displayName=effective_display_name,
      location=_DEFAULT_LOCATION,
      parent=parent,
      # The Provisioning API requires a platform details field (oneof
      # platform_details) to be set, otherwise failing with
      # MISSING_PLATFORM_DETAILS. Since this command provisions a Firebase Web
      # App, webInput is required.
      webInput=messages.WebInput(),
  )

  return client.firebase.ProvisionFirebaseApp(request)


def EnsureFirebaseAdded(
    project_id: str,
    client: base_api.BaseApiClient | None = None,
    messages: types.ModuleType | None = None,
) -> Any:
  """Ensures Firebase resources and services are enabled in the project.

  Checks whether the project is already an active Firebase project. If not,
  calls ProvisionFirebaseApp and waits for the operation to complete.

  Args:
    project_id: Google Cloud project ID.
    client: Optional Apitools client instance. If not provided, a client
      instance for v1beta1 is used.
    messages: Optional Apitools messages module. If not provided, messages
      module for v1beta1 is used.

  Returns:
    FirebaseProject: The Firebase project resource.
  """
  client = client or firebase_util.GetClientInstance(api_version='v1beta1')
  messages = messages or firebase_util.GetMessagesModule(api_version='v1beta1')

  parent = firebase_util.GetProjectRef(project_id).RelativeName()

  # Check if project already has Firebase enabled.
  try:
    return client.projects.Get(messages.FirebaseProjectsGetRequest(name=parent))
  except apitools_exceptions.HttpNotFoundError:
    pass

  # If not found, provision Firebase in the project using ProvisionFirebaseApp
  # (v1alpha) instead of AddFirebase (v1beta1). AddFirebase unconditionally
  # triggers firebaseApiEnabler.enableFirebaseApi(), which requires
  # serviceusage.services.enable and fails with HTTP 403 on Google-Hosted
  # Projects (GHPs). ProvisionFirebaseApp uses ProvisionFirebaseAppWorkflow,
  # which supports GHPs without requiring serviceusage.services.enable.
  app_namespace = (
      f'{_DEFAULT_APP_NAMESPACE_PREFIX}.{project_id.replace("-", "_")}'
  )
  try:
    operation = ProvisionFirebaseApp(
        app_namespace=app_namespace,
        display_name=project_id,
        parent=parent,
    )
  except apitools_exceptions.HttpConflictError:
    # Another caller or concurrent request already initiated or completed
    # adding Firebase.
    return client.projects.Get(messages.FirebaseProjectsGetRequest(name=parent))

  ops_client = GetClientInstance()
  poller = waiter.CloudOperationPollerNoResources(
      ops_client.operations, get_name_func=lambda x: x
  )
  waiter.WaitFor(
      poller,
      operation.name,
      f'Adding Firebase to project [{project_id}]...',
      max_wait_ms=_MAX_WAIT_MS,
      sleep_ms=_WAIT_POLL_INTERVAL_MS,
  )
  return client.projects.Get(messages.FirebaseProjectsGetRequest(name=parent))
