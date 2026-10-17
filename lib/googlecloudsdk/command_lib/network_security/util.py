# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for Data Catalog entries commands."""

from __future__ import annotations

import os

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.network_security import GetClientInstance
from googlecloudsdk.api_lib.network_security import GetMessagesModule
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.networksecurity.v1alpha1 import networksecurity_v1alpha1_messages as v1alpha1_messages
from googlecloudsdk.generated_clients.apis.networksecurity.v1beta1 import networksecurity_v1beta1_messages as v1beta1_messages


def LogRemoveItemsSuccess(response, args):
  log.status.Print(
      'Items were removed from address group [{}].'.format(args.address_group)
  )
  return response


def LogAddItemsSuccess(response, args):
  log.status.Print(
      'Items were added to address group [{}].'.format(args.address_group)
  )
  return response


def SetGlobalLocation():
  """Set default location to global."""
  return 'global'


def FormatSourceAddressGroup(_, arg, request):
  source_name = arg.source
  if os.path.basename(source_name) == source_name:
    location = os.path.dirname(request.addressGroup)
    request.cloneAddressGroupItemsRequest.sourceAddressGroup = '%s/%s' % (
        location,
        source_name,
    )
  return request


def LogCloneItemsSuccess(response, args):
  log.status.Print(
      'Items were cloned to address group [{}] from [{}].'.format(
          args.address_group, args.source
      )
  )
  return response


def ListProjectAddressGroupReferences(release_track, args):
  service = GetClientInstance(release_track).projects_locations_addressGroups
  messages = GetMessagesModule(release_track)
  request_type = (
      messages.NetworksecurityProjectsLocationsAddressGroupsListReferencesRequest
  )
  return ListAddressGroupReferences(service, request_type, args)


def ListOrganizationAddressGroupReferences(release_track, args):
  service = GetClientInstance(
      release_track
  ).organizations_locations_addressGroups
  messages = GetMessagesModule(release_track)
  request_type = (
      messages.NetworksecurityOrganizationsLocationsAddressGroupsListReferencesRequest
  )
  return ListAddressGroupReferences(service, request_type, args)


def ListAddressGroupReferences(service, request_type, args):
  address_group = args.CONCEPTS.address_group.Parse()
  request = request_type(addressGroup=address_group.RelativeName())
  return list_pager.YieldFromList(
      service,
      request,
      limit=args.limit,
      batch_size=args.page_size,
      method='ListReferences',
      field='addressGroupReferences',
      current_token_attribute='pageToken',
      next_token_attribute='nextPageToken',
      batch_size_attribute='pageSize',
  )


def ForceStartOrganizationAddressGroupProgressiveRollout(release_track, args):
  client = GetClientInstance(release_track)
  service = client.organizations_locations_global_addressGroups
  messages = GetMessagesModule(release_track)
  address_group = args.CONCEPTS.address_group.Parse()
  request = messages.NetworksecurityOrganizationsLocationsGlobalAddressGroupsForceStartProgressiveRolloutRequest(
      addressGroup=address_group.RelativeName(),
      forceStartProgressiveRolloutRequest=messages.ForceStartProgressiveRolloutRequest(),
  )
  return service.ForceStartProgressiveRollout(request)


_CreateServerTlsPolicyRequest = (
    v1alpha1_messages.NetworksecurityProjectsLocationsServerTlsPoliciesCreateRequest
    | v1beta1_messages.NetworksecurityProjectsLocationsServerTlsPoliciesCreateRequest
)


class _UnsortedMutexGroupAction(base.Action):
  """Disables alphabetical sorting on the top-level ServerTlsPolicy mutex group."""

  def AddToParser(self, parser: parser_arguments.ArgumentInterceptor) -> None:
    for argument in parser.arguments:
      if argument.is_group and argument.is_mutex:
        if any(sub_argument.is_group for sub_argument in argument.arguments):
          argument.SetSortArgs(False)


def OrderServerTlsPolicyMutexGroupHook() -> list[base.Action]:
  """Preserves declaration order of ServerTlsPolicy configuration subgroups."""
  return [_UnsortedMutexGroupAction()]


def SetServerTlsPolicyFields(
    ref: resources.Resource | None,
    args: parser_extensions.Namespace,
    request: _CreateServerTlsPolicyRequest,
) -> _CreateServerTlsPolicyRequest:
  """Populates ServerTlsPolicy fields from command line arguments."""
  del ref
  messages = GetMessagesModule(args.calliope_command.ReleaseTrack())
  if request.serverTlsPolicy is None:
    request.serverTlsPolicy = messages.ServerTlsPolicy()

  if (
      args.IsSpecified('client_validation_trust_config')
      and args.client_validation_trust_config
      and not args.client_validation_trust_config.startswith('projects/')
  ):
    if request.serverTlsPolicy.mtlsPolicy is None:
      request.serverTlsPolicy.mtlsPolicy = messages.MTLSPolicy()
    if request.parent:
      request.serverTlsPolicy.mtlsPolicy.clientValidationTrustConfig = (
          f'{request.parent}/trustConfigs/{args.client_validation_trust_config}'
      )

  if args.IsSpecified('client_validation_ca_plugin_instance'):
    if request.serverTlsPolicy.mtlsPolicy is None:
      request.serverTlsPolicy.mtlsPolicy = messages.MTLSPolicy()
    request.serverTlsPolicy.mtlsPolicy.clientValidationCa = [
        messages.ValidationCA(
            certificateProviderInstance=messages.CertificateProviderInstance(
                pluginInstance=plugin_instance
            )
        )
        for plugin_instance in args.client_validation_ca_plugin_instance
    ]

  if args.IsSpecified('client_validation_ca_grpc_endpoint'):
    if request.serverTlsPolicy.mtlsPolicy is None:
      request.serverTlsPolicy.mtlsPolicy = messages.MTLSPolicy()
    grpc_endpoint_type = messages.ValidationCA.field_by_name(
        'grpcEndpoint'
    ).type
    request.serverTlsPolicy.mtlsPolicy.clientValidationCa = [
        messages.ValidationCA(
            grpcEndpoint=grpc_endpoint_type(targetUri=target_uri)
        )
        for target_uri in args.client_validation_ca_grpc_endpoint
    ]

  return request


_PatchServerTlsPolicyRequest = (
    v1alpha1_messages.NetworksecurityProjectsLocationsServerTlsPoliciesPatchRequest
    | v1beta1_messages.NetworksecurityProjectsLocationsServerTlsPoliciesPatchRequest
)


def _AddFieldToUpdateMask(
    field: str,
    request: _PatchServerTlsPolicyRequest,
) -> None:
  """Adds a field to request.updateMask if not already present."""
  if not request.updateMask:
    request.updateMask = field
    return
  masks = request.updateMask.split(',')
  if field not in masks:
    masks.append(field)
    request.updateMask = ','.join(masks)


def UpdateServerTlsPolicyFields(
    ref: resources.Resource | None,
    args: parser_extensions.Namespace,
    request: _PatchServerTlsPolicyRequest,
) -> _PatchServerTlsPolicyRequest:
  """Updates repeated ValidationCA and clears clientValidationRelaxations on ServerTlsPolicy update requests."""
  del ref
  messages = GetMessagesModule(args.calliope_command.ReleaseTrack())
  if request.serverTlsPolicy is None:
    request.serverTlsPolicy = messages.ServerTlsPolicy()

  if args.IsSpecified('client_validation_ca_plugin_instance'):
    if request.serverTlsPolicy.mtlsPolicy is None:
      request.serverTlsPolicy.mtlsPolicy = messages.MTLSPolicy()
    request.serverTlsPolicy.mtlsPolicy.clientValidationCa = [
        messages.ValidationCA(
            certificateProviderInstance=messages.CertificateProviderInstance(
                pluginInstance=plugin_instance
            )
        )
        for plugin_instance in args.client_validation_ca_plugin_instance
    ]
    _AddFieldToUpdateMask('mtlsPolicy.clientValidationCa', request)

  if args.IsSpecified('client_validation_ca_grpc_endpoint'):
    if request.serverTlsPolicy.mtlsPolicy is None:
      request.serverTlsPolicy.mtlsPolicy = messages.MTLSPolicy()
    grpc_endpoint_type = messages.ValidationCA.field_by_name(
        'grpcEndpoint'
    ).type
    request.serverTlsPolicy.mtlsPolicy.clientValidationCa = [
        messages.ValidationCA(
            grpcEndpoint=grpc_endpoint_type(targetUri=target_uri)
        )
        for target_uri in args.client_validation_ca_grpc_endpoint
    ]
    _AddFieldToUpdateMask('mtlsPolicy.clientValidationCa', request)

  if (
      args.IsSpecified('clear_client_validation_relaxations')
      and args.clear_client_validation_relaxations
  ):
    if request.serverTlsPolicy.mtlsPolicy is None:
      request.serverTlsPolicy.mtlsPolicy = messages.MTLSPolicy()
    request.serverTlsPolicy.mtlsPolicy.clientValidationRelaxations = []
    _AddFieldToUpdateMask('mtlsPolicy.clientValidationRelaxations', request)

  return request
