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
"""Common utility functions for the firebase command group."""

import json

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.firebase import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


API_NAME = 'firebase'
DEFAULT_API_VERSION = 'v1beta1'
VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha',
    base.ReleaseTrack.BETA: 'v1beta1',
}

RULES_API_NAME = 'firebaserules'
RULES_DEFAULT_API_VERSION = 'v1'


def GetApiVersion(release_track=base.ReleaseTrack.BETA):
  """Returns the API version for the given release track."""
  return VERSION_MAP.get(release_track, DEFAULT_API_VERSION)


def _ResolveApiVersion(api_version=None, release_track=None):
  """Resolves the API version."""
  if api_version is None and release_track is not None:
    return GetApiVersion(release_track)
  elif api_version is None:
    return DEFAULT_API_VERSION
  return api_version


def GetClientInstance(api_version=None, release_track=None, no_http=False):
  """Returns a client instance for the Firebase Management API."""
  version = _ResolveApiVersion(api_version, release_track)
  return apis.GetClientInstance(API_NAME, version, no_http=no_http)


def GetMessagesModule(api_version=None, release_track=None):
  """Returns the message module for the Firebase Management API."""
  version = _ResolveApiVersion(api_version, release_track)
  return apis.GetMessagesModule(API_NAME, version)



def GetRulesClientInstance(api_version=RULES_DEFAULT_API_VERSION,
                           no_http=False):
  """Returns a client instance for the Firebase Security Rules API."""
  return apis.GetClientInstance(RULES_API_NAME, api_version, no_http=no_http)


def GetRulesMessagesModule(api_version=RULES_DEFAULT_API_VERSION):
  """Returns the message module for the Firebase Security Rules API."""
  return apis.GetMessagesModule(RULES_API_NAME, api_version)


def GetClientClass(api_version=DEFAULT_API_VERSION):
  """Returns the client class for the Firebase Management API."""
  version = _ResolveApiVersion(api_version=api_version)
  return apis.GetClientClass(API_NAME, version)



def GetRulesClientClass(api_version=RULES_DEFAULT_API_VERSION):
  """Returns the client class for the Firebase Security Rules API."""
  return apis.GetClientClass(RULES_API_NAME, api_version)


def GetProjectRef(project_id, api_version=None, release_track=None):
  """Returns a resource reference for a Firebase project."""
  version = _ResolveApiVersion(
      api_version=api_version, release_track=release_track
  )
  return resources.REGISTRY.Parse(
      project_id,
      collection='firebase.projects',
      api_version=version,
  )


def GetFormattedErrorMessage(error):
  """Parses and returns a formatted error message from an Apitools HttpError."""
  if not isinstance(error, apitools_exceptions.HttpError):
    return str(error)
  try:
    data = json.loads(error.content)
    if isinstance(data, dict):
      err_val = data.get('error')
      if isinstance(err_val, dict) and 'message' in err_val:
        return err_val['message']
  except (ValueError, TypeError, KeyError):
    pass
  return str(error)


def HandleHttpError(error):
  """Translates an Apitools HttpError to a user-facing Firebase HttpException."""
  if isinstance(error, exceptions.FirebaseError):
    raise error
  if isinstance(error, apitools_exceptions.HttpError):
    msg = GetFormattedErrorMessage(error)
    raise exceptions.HttpException(msg) from error
  raise error
