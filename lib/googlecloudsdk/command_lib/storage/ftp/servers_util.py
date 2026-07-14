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
"""Utilities for Cloud FTP servers."""

from googlecloudsdk.core import properties


def GetParentString(location):
  """Constructs parent resource string."""
  project = properties.VALUES.core.project.Get(required=True)
  return 'projects/{}/locations/{}'.format(project, location.lower())


def GetServerResourceName(location, server_id):
  """Constructs server resource name."""
  parent = GetParentString(location)
  return '{}/servers/{}'.format(parent, server_id)


def ParseConsumerAcceptList(messages, accept_dict):
  """Parses consumer-accept-list ArgDict."""
  if not accept_dict:
    return None
  consumer_list = []
  for project, limit in accept_dict.items():
    if not project.startswith('projects/'):
      project = 'projects/{}'.format(project)
    consumer_list.append(
        messages.AllowedConsumer(project=project, connectionLimit=int(limit))
    )
  return consumer_list


def ParseConsumerRejectList(messages, reject_list):
  """Parses consumer-reject-list ArgList."""
  if not reject_list:
    return None
  consumer_list = []
  for project in reject_list:
    if not project.startswith('projects/'):
      project = 'projects/{}'.format(project)
    consumer_list.append(messages.DeniedConsumer(project=project))
  return consumer_list


def CreateServerMsg(messages, args):
  """Constructs Server message for Create API."""
  access_type_enum = getattr(
      messages.Server.AccessTypeValueValuesEnum, args.access_type.upper()
  )
  server_msg = messages.Server(
      displayName=args.display_name,
      accessType=access_type_enum,
  )

  if access_type_enum == messages.Server.AccessTypeValueValuesEnum.EXTERNAL:
    if not args.allowed_cidr_blocks:
      raise ValueError(
          '--allowed-cidr-blocks is required for EXTERNAL access type.'
      )
    server_msg.externalConfig = messages.ExternalServerConfig(
        allowedCidrBlocks=args.allowed_cidr_blocks
    )
  elif access_type_enum == messages.Server.AccessTypeValueValuesEnum.INTERNAL:
    if not args.consumer_accept_list:
      raise ValueError(
          '--consumer-accept-list is required for INTERNAL access type.'
      )
    accept_list = ParseConsumerAcceptList(messages, args.consumer_accept_list)
    reject_list = ParseConsumerRejectList(messages, args.consumer_reject_list)
    server_msg.internalConfig = messages.InternalServerConfig(
        consumerAcceptList=accept_list,
        consumerRejectList=reject_list,
    )

  return server_msg


def UpdateServerMsg(messages, args, existing_server):
  """Constructs Server message and update_mask for Update API."""
  server_msg = messages.Server(name=existing_server.name)
  update_mask = []

  if args.IsSpecified('display_name'):
    server_msg.displayName = args.display_name
    update_mask.append('displayName')

  if (
      existing_server.accessType
      == messages.Server.AccessTypeValueValuesEnum.EXTERNAL
  ):
    if args.IsSpecified('allowed_cidr_blocks'):
      server_msg.externalConfig = messages.ExternalServerConfig(
          allowedCidrBlocks=args.allowed_cidr_blocks
      )
      update_mask.append('externalConfig.allowedCidrBlocks')
  elif (
      existing_server.accessType
      == messages.Server.AccessTypeValueValuesEnum.INTERNAL
  ):
    internal_config = messages.InternalServerConfig()
    modified = False
    if args.IsSpecified('consumer_accept_list'):
      internal_config.consumerAcceptList = ParseConsumerAcceptList(
          messages, args.consumer_accept_list
      )
      update_mask.append('internalConfig.consumerAcceptList')
      modified = True
    if args.IsSpecified('consumer_reject_list'):
      internal_config.consumerRejectList = ParseConsumerRejectList(
          messages, args.consumer_reject_list
      )
      update_mask.append('internalConfig.consumerRejectList')
      modified = True
    if modified:
      server_msg.internalConfig = internal_config

  if not update_mask:
    raise ValueError(
        'No fields specified to update for server [{}].'.format(args.SERVER_ID)
    )

  return server_msg, update_mask
