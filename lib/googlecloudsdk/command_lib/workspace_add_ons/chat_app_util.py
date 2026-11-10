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
"""Utilities for `gcloud workspace-add-ons chat-app-config` commands."""


from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import yaml

_API_NAME = 'gsuiteaddons'
_API_VERSION = 'v1'

_CONFIG_FILE_FLAG = '--config-file'

# Setting --dialogflow-edition (or the Dialogflow branch in a config file)
# replaces the whole Dialogflow configuration, so that switching from CX to ES
# drops the agent instead of keeping the old one.
_DIALOGFLOW_PATH = (
    'interactiveFeatureConfig.connectionConfig.dialogflowEndpointConfig')

# The resource name is immutable and comes from --project.
_IGNORED_FILE_FIELDS = frozenset(['name'])

_TESTING_PRINCIPALS_PATH = (
    'interactiveFeatureConfig.allowlistedTestingPrincipals')


def _MaskPaths(data, prefix=''):
  """Returns the update mask paths for the fields present in a config dict.

  Nested objects are walked, so that a file that sets one nested field doesn't
  clear its siblings. Lists and empty objects are leaves: the API replaces a
  list as a whole, and an empty value clears the field.

  Args:
    data: dict, the parsed config file, or a nested object inside it.
    prefix: str, the dotted path of `data` inside the config.

  Returns:
    A set of dotted field paths.
  """
  paths = set()
  for key, value in data.items():
    path = prefix + key
    if isinstance(value, dict) and value:
      paths.update(_MaskPaths(value, path + '.'))
    else:
      paths.add(path)
  return paths


def _NormalizeMask(paths):
  """Widens Dialogflow paths to the whole Dialogflow configuration."""
  normalized = set()
  for path in paths:
    if path.startswith(_DIALOGFLOW_PATH + '.'):
      normalized.add(_DIALOGFLOW_PATH)
    else:
      normalized.add(path)
  return normalized


def _SplitMask(mask):
  return {path for path in (mask or '').split(',') if path}


def ParseConfigFileHook(unused_ref, args, request):
  """Sets the Chat app configuration and update mask from --config-file.

  The update mask lists the fields present in the file, so fields that aren't
  in the file are left unchanged, and a field that is present with an empty
  value is cleared. The `name` field is ignored: the target project comes from
  --project. Fields that this gcloud version doesn't know about are rejected
  before any API call.

  Args:
    unused_ref: reference to the Chat app configuration.
    args: command line arguments.
    request: API request to be issued.

  Returns:
    The modified request.

  Raises:
    calliope_exceptions.InvalidArgumentException: if the file can't be parsed
      into a Chat app configuration, or doesn't set any field.
  """
  del unused_ref  # Unused.
  if not args.IsSpecified('config_file'):
    return request

  try:
    data = yaml.load(args.config_file)
  except yaml.YAMLParseError as e:
    raise calliope_exceptions.InvalidArgumentException(
        _CONFIG_FILE_FLAG,
        'The file must be valid YAML or JSON: {}'.format(e))
  if data is None:
    data = {}
  if not isinstance(data, dict):
    raise calliope_exceptions.InvalidArgumentException(
        _CONFIG_FILE_FLAG,
        'The file must contain an object with Chat app configuration fields.')

  fields = {
      key: value
      for key, value in data.items()
      if key not in _IGNORED_FILE_FIELDS
  }
  if not fields:
    raise calliope_exceptions.InvalidArgumentException(
        _CONFIG_FILE_FLAG,
        "The file doesn't set any Chat app configuration fields.")

  messages = apis.GetMessagesModule(_API_NAME, _API_VERSION)
  try:
    config = messages_util.DictToMessageWithErrorCheck(
        fields, messages.GoogleCloudGsuiteaddonsV1ChatAppConfig)
  except messages_util.DecodeError as e:
    raise calliope_exceptions.InvalidArgumentException(
        _CONFIG_FILE_FLAG,
        '{}\nCheck the field names against the output of `describe`, or run '
        '`gcloud components update` if the field is new.'.format(e))
  except AttributeError as e:
    # apitools raises AttributeError when a value that should be an object
    # isn't one (b/77547931).
    raise calliope_exceptions.InvalidArgumentException(
        _CONFIG_FILE_FLAG,
        'A field in the file has a value of the wrong type. Compare the file '
        'with the output of `describe`.') from e

  config.name = request.name
  request.googleCloudGsuiteaddonsV1ChatAppConfig = config
  request.updateMask = ','.join(sorted(_NormalizeMask(_MaskPaths(fields))))
  return request


def AddClearedFieldsToMaskHook(unused_ref, args, request):
  """Finishes the update mask built from the per-field flags.

  Adds `avatarUri` when --clear-avatar-uri is passed, leaving the field empty
  in the request so that the API resets the app to the default avatar. Also
  widens the Dialogflow paths, because --dialogflow-edition replaces the whole
  Dialogflow configuration.

  Args:
    unused_ref: reference to the Chat app configuration.
    args: command line arguments.
    request: API request to be issued.

  Returns:
    The modified request.
  """
  del unused_ref  # Unused.
  paths = _SplitMask(request.updateMask)
  if args.IsSpecified('clear_avatar_uri'):
    paths.add('avatarUri')
  request.updateMask = ','.join(sorted(_NormalizeMask(paths)))
  return request


def _GetAllowlistedTestingPrincipals(name):
  """Returns the testing principals of the current Chat app configuration.

  Args:
    name: str, resource name of the Chat app configuration.

  Returns:
    A list of email addresses. It's empty if the project doesn't have a Chat
    app yet or the app doesn't have testing principals.
  """
  client = apis.GetClientInstance(_API_NAME, _API_VERSION)
  get_request_type = (
      client.MESSAGES_MODULE.GsuiteaddonsProjectsChatAppConfigGetRequest)
  # The API's default BASIC view leaves out interactiveFeatureConfig.
  config = client.projects_chatAppConfig.Get(
      get_request_type(
          name=name, view=get_request_type.ViewValueValuesEnum.FULL))
  if config.interactiveFeatureConfig is None:
    return []
  return list(config.interactiveFeatureConfig.allowlistedTestingPrincipals)


def _PrincipalKey(principal):
  """Returns the key that identifies a testing principal.

  Google Workspace treats email addresses as case-insensitive, and the API can
  return addresses with leading spaces.

  Args:
    principal: str, an email address.

  Returns:
    The address without surrounding spaces, in lowercase.
  """
  return principal.strip().lower()


def UpdateAllowlistedTestingPrincipalsHook(unused_ref, args, request):
  """Applies the flags that add, remove, or clear testing principals.

  The API replaces a list as a whole, so the request carries the complete new
  list, and only this field is added to the update mask. The new list starts
  from the app's current list, which is read first, unless
  --clear-allowlisted-testing-principals is passed, in which case it starts
  empty. Principals in --remove-allowlisted-testing-principals are then
  dropped, and principals in --add-allowlisted-testing-principals that aren't
  in the list yet are appended.

  Args:
    unused_ref: reference to the Chat app configuration.
    args: command line arguments.
    request: API request to be issued.

  Returns:
    The modified request.
  """
  del unused_ref  # Unused.
  add_specified = args.IsSpecified('add_allowlisted_testing_principals')
  remove_specified = args.IsSpecified('remove_allowlisted_testing_principals')
  clear_specified = args.IsSpecified('clear_allowlisted_testing_principals')
  if not (add_specified or remove_specified or clear_specified):
    return request

  if clear_specified:
    principals = []
  else:
    removed = {
        _PrincipalKey(principal)
        for principal in (args.remove_allowlisted_testing_principals or [])
    }
    principals = [
        principal
        for principal in _GetAllowlistedTestingPrincipals(request.name)
        if _PrincipalKey(principal) not in removed
    ]
  present = {_PrincipalKey(principal) for principal in principals}
  for principal in args.add_allowlisted_testing_principals or []:
    principal = principal.strip()
    if principal and _PrincipalKey(principal) not in present:
      principals.append(principal)
      present.add(_PrincipalKey(principal))

  messages = apis.GetMessagesModule(_API_NAME, _API_VERSION)
  if request.googleCloudGsuiteaddonsV1ChatAppConfig is None:
    request.googleCloudGsuiteaddonsV1ChatAppConfig = (
        messages.GoogleCloudGsuiteaddonsV1ChatAppConfig())
  config = request.googleCloudGsuiteaddonsV1ChatAppConfig
  if config.interactiveFeatureConfig is None:
    config.interactiveFeatureConfig = (
        messages.GoogleCloudGsuiteaddonsV1InteractiveFeatureConfig())
  config.interactiveFeatureConfig.allowlistedTestingPrincipals = principals

  paths = _SplitMask(request.updateMask)
  paths.add(_TESTING_PRINCIPALS_PATH)
  request.updateMask = ','.join(sorted(paths))
  return request
