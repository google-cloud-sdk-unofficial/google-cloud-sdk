# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""API Keys API helper functions."""


from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base

_PROJECT_RESOURCE = 'projects/%s'
_PARENT_RESOURCE = 'projects/%s/locations/global'
_API_NAME = 'apikeys'

_RELEASE_TRACK_TO_API_VERSION = {
    calliope_base.ReleaseTrack.ALPHA: 'v2',
    calliope_base.ReleaseTrack.BETA: 'v2',
    calliope_base.ReleaseTrack.GA: 'v2'
}


def ListKeys(
    project,
    show_deleted=None,
    page_size=None,
    limit=None,
    release_track=calliope_base.ReleaseTrack.GA,
):
  """List API Keys for a given project.

  Args:
    project: The project for which to list keys.
    show_deleted: Includes deleted keys in the list.
    page_size: The page size to list.
    limit: The max number of metrics to return.
    release_track: The release track of the command.

  Raises:
    exceptions.PermissionDeniedException: when listing keys fails.

  Returns:
    The list of keys
  """
  client = GetClientInstance(release_track)
  messages = client.MESSAGES_MODULE

  request = messages.ApikeysProjectsLocationsKeysListRequest(
      parent=GetParentResourceName(project), showDeleted=show_deleted
  )
  return list_pager.YieldFromList(
      client.projects_locations_keys,
      request,
      limit=limit,
      batch_size_attribute='pageSize',
      batch_size=page_size,
      field='keys',
  )


def GetClientInstance(release_track=calliope_base.ReleaseTrack.GA):
  """Returns an API client for ApiKeys."""
  api_version = _RELEASE_TRACK_TO_API_VERSION.get(release_track)
  return core_apis.GetClientInstance(_API_NAME, api_version)


def GetMessagesModule(release_track=calliope_base.ReleaseTrack.GA):
  """Returns the messages module for ApiKeys."""
  api_version = _RELEASE_TRACK_TO_API_VERSION.get(release_track)
  return core_apis.GetMessagesModule(_API_NAME, api_version)


def GetOperation(name, release_track=calliope_base.ReleaseTrack.GA):
  """Make API call to get an operation.

  Args:
    name: The name of the operation.
    release_track: The release track of the command.

  Raises:
    exceptions.OperationErrorException: when the getting operation API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The result of the operation
  """
  client = GetClientInstance(release_track)
  messages = client.MESSAGES_MODULE
  request = messages.ApikeysOperationsGetRequest(name=name)
  try:
    return client.operations.Get(request)
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(e, exceptions.OperationErrorException)


def _ResolveMessageClass(messages, candidates):
  """Safely resolves the first matching message class from a messages module."""
  for candidate in candidates:
    if hasattr(messages, candidate):
      return getattr(messages, candidate)
  raise AttributeError(
      f'None of the candidate message classes {candidates} found in messages'
      ' module.'
  )


def GetAllowedAndroidApplications(args, messages):
  """Create list of allowed android applications."""
  allowed_applications = []
  entries = getattr(args, 'allowed_application', []) or []
  if not entries:
    return allowed_applications
  app_cls = _ResolveMessageClass(
      messages,
      [
          'V2AndroidApplication',
          'AndroidApplication',
          'V3AndroidApplication',
      ],
  )
  for application in entries:
    android_application = app_cls(
        sha1Fingerprint=application['sha1_fingerprint'],
        packageName=application['package_name'],
    )
    allowed_applications.append(android_application)
  return allowed_applications


def GetApiTargets(args, messages):
  """Create list of target apis."""
  api_targets = []
  entries = getattr(args, 'api_target', []) or []
  if not entries:
    return api_targets
  target_cls = _ResolveMessageClass(
      messages,
      [
          'V2ApiTarget',
          'ApiTarget',
          'V3ApiTarget',
      ],
  )
  for api_target in entries:
    api_targets.append(
        target_cls(
            service=api_target.get('service'),
            methods=api_target.get('methods', []),
        )
    )
  return api_targets


def GetAnnotations(args, messages):
  """Create list of annotations."""
  annotations = getattr(args, 'annotations', {})
  if not annotations:
    return None

  key_cls = _ResolveMessageClass(
      messages,
      [
          'V2Key',
          'Key',
          'V3Key',
      ],
  )

  additional_property_messages = []
  for key, value in annotations.items():
    additional_property_messages.append(
        key_cls.AnnotationsValue.AdditionalProperty(key=key, value=value)
    )

  annotation_value_message = key_cls.AnnotationsValue(
      additionalProperties=additional_property_messages
  )

  return annotation_value_message


def GetParentResourceName(project):
  return _PARENT_RESOURCE % (project)

