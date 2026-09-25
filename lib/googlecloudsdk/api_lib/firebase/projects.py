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

from googlecloudsdk.api_lib.util import apis

_API_NAME = 'firebase'
_API_VERSION = 'v1alpha'
_DEFAULT_LOCATION = 'us-west1'


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
  )

  return client.firebase.ProvisionFirebaseApp(request)
