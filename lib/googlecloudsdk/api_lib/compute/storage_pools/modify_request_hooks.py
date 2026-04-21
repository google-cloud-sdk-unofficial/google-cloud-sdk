# -*- coding: utf-8 -*- #
# Copyright 2023 Google Inc. All Rights Reserved.
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
"""Modify request hooks, specifically for storage-pool related ones."""

import json
from typing import Any, List, Optional

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions


# Share settings only supported in alpha for now.
API_VERSION_BY_RELEASE_TRACK = {
    base.ReleaseTrack.ALPHA: 'alpha',
}


def add_name_to_payload(resource_ref: Any, _, request_msg: Any) -> Any:
  """Modify the request message, carrying resource name into it.

  Args:
    resource_ref: the resource reference.
    request_msg: the request message constructed by the framework
  Returns:
    the modified request message.
  """
  request_msg.storagePool.name = resource_ref.storagePool
  return request_msg


def _get_messages(args: Any) -> Any:
  """Get messages module based on release track."""
  track = args.calliope_command.ReleaseTrack()
  api_version = API_VERSION_BY_RELEASE_TRACK.get(track, 'alpha')
  return apis.GetMessagesModule('compute', api_version)


def _validate_project_list_flag(args: Any, flag_name: str) -> None:
  """Validates that the project list flag is not empty and contains non-empty projects."""
  flag_value = getattr(args, flag_name, None)
  cli_flag_name = '--' + flag_name.replace('_', '-')
  if flag_value == [] or not all(p and p.strip() for p in flag_value):
    raise exceptions.InvalidArgumentException(
        cli_flag_name,
        'The {} list must contain at least one non-empty Project ID or project '
        'number. Project IDs or numbers in the list cannot be empty.'
        .format(cli_flag_name),
    )


def _create_project_map(
    messages: Any,
    *,
    projects_to_add: Optional[List[str]] = None,
    projects_to_remove: Optional[List[str]] = None
) -> Any:
  """Creates a ProjectMapValue object for ShareSettings.

  This can be used for create (POST) or update (PATCH) operations, building
  the projectMap based on projects to add and projects to remove.

  Args:
    messages: The API messages module.
    projects_to_add: A list of project IDs to add to the share settings.
    projects_to_remove: A list of project IDs to remove from the share
      settings (by setting their value to null in PATCH).

  Returns:
    A messages.StoragePoolShareSettings.ProjectMapValue object.
  """
  projects_to_add = set(projects_to_add or [])
  projects_to_remove = set(projects_to_remove or [])
  project_map_entry_type = (
      messages.StoragePoolShareSettings.ProjectMapValue.AdditionalProperty
  )
  project_info_type = messages.StoragePoolShareSettingsProjectConfig

  removed_properties = [
      project_map_entry_type(key=project, value=None)
      for project in projects_to_remove
  ]
  added_properties = [
      project_map_entry_type(
          key=project, value=project_info_type(projectId=project)
      )
      for project in projects_to_add
  ]

  properties = sorted(
      removed_properties + added_properties, key=lambda p: p.key
  )

  return messages.StoragePoolShareSettings.ProjectMapValue(
      additionalProperties=properties
  )


def add_shared_with_to_payload(_, args: Any, request_msg: Any) -> Any:
  """Modify the request message, adding shared-with projects to it.

  Args:
    _: the resource reference. Type: resources.Resource.
    args: parsed command-line arguments. Type: argparse.Namespace.
    request_msg: the request message constructed by the framework. Type:
      compute.storagePools.insert message.

  Returns:
    the modified request message.

  Raises:
    exceptions.InvalidArgumentException: If share-with list is invalid.
  """
  if not args.IsSpecified('share_with'):
    return request_msg

  _validate_project_list_flag(args, 'share_with')

  messages = _get_messages(args)
  share_settings = messages.StoragePoolShareSettings(
      projectMap=_create_project_map(messages, projects_to_add=args.share_with),
  )
  request_msg.storagePool.shareSettings = share_settings
  return request_msg


def _remove_share_with_encoder(
    message: Any, unused_encoder: Optional[Any] = None
) -> str:
  """Encoder for use when removing a share with.

  It ensures that properties with null values are correctly encoded in the
  JSON payload for PATCH requests.

  Args:
    message: The message to encode.
    unused_encoder: The base encoder, unused.

  Returns:
    JSON string representation of the message.
  """
  res = {
      prop.key: None if prop.value is None else encoding.MessageToDict(prop.value)
      for prop in message.additionalProperties
  }
  return json.dumps(res)


def _remove_share_with_decoder(s: Any, messages: Any) -> Any:
  """Decoder for use when removing a share with.

  It works around issues with proto encoding of AdditionalProperties with null
  values by directly decoding a dict of keys with None values into json,
  skipping proto-based decoding.

  Args:
    s: a string representing a JSON dictionary of keys with None values.
    messages: The API messages module.

  Returns:
    A messages.StoragePoolShareSettings.ProjectMapValue object.
  """
  if not isinstance(s, (str, bytes)):
    return s
  py_object = json.loads(s)
  return _create_project_map(messages, projects_to_add=py_object.keys())


def modify_share_settings(_, args: Any, request_msg: Any) -> Any:
  """Hook to modify share settings for storage pool update requests.

  This function updates the request message to include changes to the storage
  pool's share settings based on the `--add-share-with` and
  `--remove-share-with` flags. It also registers custom JSON encoders/decoders
  to handle the removal of projects by setting their values to null in the
  ProjectMap. The 'shareSettings' field is added to the update mask.

  Args:
    _: The resource reference (unused).
    args: The parsed command-line arguments. Expected to contain
      `add_share_with` and `remove_share_with` attributes if specified by the
      user.
    request_msg: The API request message constructed by the framework. This
      message is typically a compute.storagePools.patch or similar update
      message.

  Returns:
    The modified request message with updated share settings and update mask.

  Raises:
    exceptions.InvalidArgumentException: If:
      -   The lists provided to `--add-share-with` or `--remove-share-with`
          contain empty or invalid project IDs.
      -   The same project ID appears in both `--add-share-with` and
          `--remove-share-with`.
  """
  if not args.IsSpecified('add_share_with') and not args.IsSpecified(
      'remove_share_with'
  ):
    return request_msg
  messages = _get_messages(args)

  if args.IsSpecified('remove_share_with'):
    _validate_project_list_flag(args, 'remove_share_with')
    def decoder(s: Any) -> Any:
      return _remove_share_with_decoder(s, messages)
    encoding.RegisterCustomMessageCodec(
        encoder=_remove_share_with_encoder, decoder=decoder
    )(messages.StoragePoolShareSettings.ProjectMapValue)

  if args.IsSpecified('add_share_with'):
    _validate_project_list_flag(args, 'add_share_with')

  added = set(args.add_share_with or [])
  removed = set(args.remove_share_with or [])
  common = sorted(added.intersection(removed))
  if common:
    raise exceptions.InvalidArgumentException(
        '--add-share-with, --remove-share-with',
        '--add-share-with and --remove-share-with should contain different'
        f' project ids. projects: {", ".join(common)} showed up'
        ' in both flag lists',
    )

  share_settings = messages.StoragePoolShareSettings(
      projectMap=_create_project_map(
          messages,
          projects_to_add=args.add_share_with,
          projects_to_remove=args.remove_share_with,
      ),
  )
  if request_msg.storagePoolResource is None:
    request_msg.storagePoolResource = messages.StoragePool()
  request_msg.storagePoolResource.shareSettings = share_settings

  current_masks = (
      set(request_msg.updateMask.split(','))
      if request_msg.updateMask
      else set()
  )
  current_masks.add('shareSettings')
  request_msg.updateMask = ','.join(sorted(filter(None, current_masks)))
  return request_msg
