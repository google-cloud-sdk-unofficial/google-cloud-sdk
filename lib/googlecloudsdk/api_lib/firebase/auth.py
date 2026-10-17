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
"""API client helper for Firebase Auth management."""

import urllib.parse

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.firebase import exceptions as firebase_exceptions
from googlecloudsdk.api_lib.firebase import util as firebase_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions


def ValidateRedirectUris(redirect_uris):
  """Validates and normalizes redirect URIs as HTTP/HTTPS URLs.

  Prepends 'http://' to any URI that does not specify a scheme.

  Args:
    redirect_uris: list of str, The redirect URIs to validate and normalize.

  Returns:
    list of str, The normalized redirect URIs.

  Raises:
    calliope_exceptions.InvalidArgumentException: If any URI is empty or does
      not have an http or https scheme and a non-empty hostname.
  """
  if not redirect_uris:
    return []
  normalized_uris = []
  for uri in redirect_uris:
    if not uri or not uri.strip():
      raise calliope_exceptions.InvalidArgumentException(
          '--redirect-uris',
          'Redirect URI cannot be empty. Each URI must be a valid URL'
          ' starting with http:// or https:// (e.g. https://example.com).',
      )
    normalized_uri = uri if '://' in uri else f'http://{uri}'
    try:
      parsed = urllib.parse.urlsplit(normalized_uri)
    except ValueError as e:
      raise calliope_exceptions.InvalidArgumentException(
          '--redirect-uris',
          f'Invalid redirect URI [{uri}]: {e}. Each URI must be a valid URL'
          ' starting with http:// or https:// (e.g. https://example.com).',
      ) from e
    if parsed.scheme.lower() not in ('http', 'https') or not parsed.hostname:
      raise calliope_exceptions.InvalidArgumentException(
          '--redirect-uris',
          f'Invalid redirect URI [{uri}]. Each URI must be a valid URL'
          ' starting with http:// or https:// (e.g. https://example.com).',
      )
    normalized_uris.append(normalized_uri)
  return normalized_uris


class FirebaseAuthOperationPoller(waiter.OperationPoller):
  """Poller for Firebase Auth long running operations."""

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


class AuthClient:
  """Client for Firebase Auth management API."""

  def __init__(
      self,
      client=None,
      messages=None,
      api_version=None,
      release_track=None,
  ):
    if api_version is None:
      if release_track in (base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA):
        api_version = 'v1alpha'
      elif release_track is not None:
        api_version = firebase_util.GetApiVersion(release_track)
      else:
        api_version = 'v1alpha'
    self.client = client or firebase_util.GetClientInstance(
        api_version=api_version
    )
    self.messages = messages or firebase_util.GetMessagesModule(
        api_version=api_version
    )

  def EnableGoogleSignIn(
      self,
      project_id,
      app_id,
      display_name=None,
      support_email=None,
      client_id=None,
      client_secret=None,
      redirect_uris=None,
  ):
    """Enable and configure Google Sign-In for Firebase Authentication.

    Args:
      project_id: str, Google Cloud project ID.
      app_id: str, Firebase App ID.
      display_name: str, Optional display name for OAuth brand.
      support_email: str, Optional support email for OAuth brand.
      client_id: str, Optional existing OAuth client ID.
      client_secret: str, Optional existing OAuth client secret.
      redirect_uris: list of str, Optional authorized redirect URIs.

    Returns:
      Operation: The raw long-running operation message.
    """
    normalized_redirect_uris = ValidateRedirectUris(redirect_uris)
    parent = firebase_util.GetProjectRef(project_id).RelativeName()

    provider_mode = (
        self.messages.FirebaseAuthInput.GoogleSigninProviderModeValueValuesEnum.PROVIDER_ENABLED
    )
    provider_config = self.messages.GoogleSigninProviderConfig(
        publicDisplayName=display_name,
        customerSupportEmail=support_email,
        oauthClientId=client_id,
        oauthClientSecret=client_secret,
        oauthRedirectUris=normalized_redirect_uris,
    )

    auth_input = self.messages.FirebaseAuthInput(
        googleSigninProviderMode=provider_mode,
        googleSigninProviderConfig=provider_config,
    )

    req = self.messages.ProvisionFirebaseAppRequest(
        parent=parent,
        appNamespace=app_id,
        firebaseAuthInput=auth_input,
        webInput=self.messages.WebInput(),
    )

    try:
      return self.client.firebase.ProvisionFirebaseApp(req)
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)
