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
"""Utilities for Cloud FTP users."""

import json
from googlecloudsdk.command_lib.storage.ftp import servers_util


def GetUserResourceName(location, server_id, user_id):
  """Constructs user resource name."""
  server_name = servers_util.GetServerResourceName(location, server_id)
  return '{}/users/{}'.format(server_name, user_id)


def ParseStorageDirectoryMappings(messages, mapping_list):
  """Parses repeated ArgDict for storage-directory-mapping."""
  if not mapping_list:
    return None
  res = []
  for mapping in mapping_list:
    if 'permission' not in mapping:
      raise ValueError(
          'Each storage directory mapping must include a "permission" key.'
      )
    perm_enum = getattr(
        messages.StorageDirectoryMapping.PermissionValueValuesEnum,
        mapping['permission'].upper(),
    )
    msg = messages.StorageDirectoryMapping(
        bucket=mapping['bucket'],
        directory=mapping['directory'],
        permission=perm_enum,
    )
    if 'bucket_prefix' in mapping:
      msg.bucketPrefix = mapping['bucket_prefix']
    res.append(msg)
  return res


def ParseUserCredentials(messages, creds_json_str):
  """Parses JSON string for user-credentials-from-file."""
  if not creds_json_str:
    return None
  try:
    creds_list = json.loads(creds_json_str)
  except json.JSONDecodeError as e:
    raise ValueError(
        'Invalid JSON format in user credentials file: {}'.format(e)
    ) from e
  res = []
  for cred in creds_list:
    type_enum = getattr(
        messages.UserCredential.CredentialTypeValueValuesEnum,
        cred['credentialType'].upper(),
    )
    msg = messages.UserCredential(
        credentialName=cred['credentialName'],
        credentialType=type_enum,
    )
    if 'sshPublicKeyBody' in cred:
      msg.sshPublicKeyBody = cred['sshPublicKeyBody']
    res.append(msg)
  return res


def CreateUserMsg(messages, args):
  """Constructs User message for Create API."""
  creds = ParseUserCredentials(messages, args.user_credentials_from_file)
  mappings = ParseStorageDirectoryMappings(
      messages, args.storage_directory_mapping
  )
  return messages.User(
      customerServiceAccount=args.customer_service_account,
      userCredentials=creds or [],
      storageDirectoryMappings=mappings or [],
  )


def UpdateUserMsg(messages, args, existing_user):
  """Constructs User message and update_mask for Update API."""
  user_msg = messages.User(name=existing_user.name)
  update_mask = []

  if args.IsSpecified('customer_service_account'):
    user_msg.customerServiceAccount = args.customer_service_account
    update_mask.append('customerServiceAccount')

  if args.IsSpecified('user_credentials_from_file'):
    user_msg.userCredentials = (
        ParseUserCredentials(messages, args.user_credentials_from_file) or []
    )
    update_mask.append('userCredentials')

  if args.IsSpecified('storage_directory_mapping'):
    user_msg.storageDirectoryMappings = (
        ParseStorageDirectoryMappings(messages, args.storage_directory_mapping)
        or []
    )
    update_mask.append('storageDirectoryMappings')

  if not update_mask:
    raise ValueError(
        'No fields specified to update for user [{}].'.format(args.USER_ID)
    )

  return user_msg, update_mask
