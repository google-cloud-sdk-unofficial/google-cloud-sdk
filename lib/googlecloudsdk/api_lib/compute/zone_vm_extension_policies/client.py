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
"""Zone VM extension policy client adapter."""

from typing import Any, Optional, Sequence
from googlecloudsdk.api_lib.compute import client_adapter
from googlecloudsdk.api_lib.compute.vm_extension_policies import scope as scope_lib
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import resources


class ZoneVmExtensionPolicy(object):
  """A zone VM extension policy, in whichever container scope owns it.

  Project, folder, and organization policies are served by three separate
  Compute services whose requests differ only in the parent field. This class
  picks the service matching the scope it was built with, so that commands stay
  unaware of the split.
  """

  def __init__(
      self,
      compute_client: client_adapter.ClientAdapter,
      policy_scope: scope_lib.Scope,
      zone: str,
      name: Optional[str] = None,
  ):
    """Creates a client for the policies of one zone in one container scope.

    Args:
      compute_client: the compute client to send the requests with.
      policy_scope: the container that owns the policy.
      zone: the zone the policy lives in.
      name: the name of the policy, for the requests that target a single one.
        Collection level requests, such as List, leave it unset.
    """
    self._compute_client = compute_client
    self._scope = policy_scope
    self._zone = zone
    self._name = name

  @classmethod
  def FromRef(
      cls,
      ref: resources.Resource,
      compute_client: client_adapter.ClientAdapter,
  ) -> 'ZoneVmExtensionPolicy':
    """Returns a client for the policy the resource reference points at."""
    return cls(compute_client, scope_lib.Scope.FromRef(ref), ref.zone,
               ref.Name())

  @classmethod
  def FromArgs(
      cls,
      args: parser_extensions.Namespace,
      compute_client: client_adapter.ClientAdapter,
  ) -> 'ZoneVmExtensionPolicy':
    """Returns a client for the policies the command's flags select."""
    return cls(compute_client, scope_lib.Scope.FromArgs(args), args.zone)

  @property
  def _client(self) -> Any:
    return self._compute_client.apitools_client

  @property
  def _messages(self) -> Any:
    return self._compute_client.messages

  def _MakeRequest(
      self,
      method: str,
      project_request: str,
      folder_request: str,
      organization_request: str,
      **kwargs,
  ) -> Sequence[Any]:
    """Sends `method` to the service that matches this client's scope.

    The request messages are named rather than passed, because the folder and
    organization ones only exist in the alpha API: resolving all three up front
    would break the project path on the tracks that do not have them yet.

    Args:
      method: the name of the method to call on the service.
      project_request: the request message name of the project service.
      folder_request: the request message name of the folder service.
      organization_request: the request message name of the organization
        service.
      **kwargs: the request fields beyond the parent and the zone, which every
        request carries.

    Returns:
      The response of the call.
    """
    if self._scope.is_folder:
      service = self._client.folderZoneVmExtensionPolicies
      parent = {'folder': self._scope.folder}
      request_name = folder_request
    elif self._scope.is_organization:
      service = self._client.organizationZoneVmExtensionPolicies
      parent = {'organization': self._scope.organization}
      request_name = organization_request
    else:
      service = self._client.zoneVmExtensionPolicies
      parent = {'project': self._scope.project}
      request_name = project_request
    request = getattr(self._messages, request_name)(
        zone=self._zone, **parent, **kwargs
    )
    return self._compute_client.MakeRequests([(service, method, request)])

  def Insert(self, policy: Any) -> Sequence[Any]:
    """Creates the policy."""
    return self._MakeRequest(
        'Insert',
        'ComputeZoneVmExtensionPoliciesInsertRequest',
        'ComputeFolderZoneVmExtensionPoliciesInsertRequest',
        'ComputeOrganizationZoneVmExtensionPoliciesInsertRequest',
        vmExtensionPolicy=policy,
    )

  def Update(self, policy: Any) -> Sequence[Any]:
    """Updates the policy."""
    return self._MakeRequest(
        'Update',
        'ComputeZoneVmExtensionPoliciesUpdateRequest',
        'ComputeFolderZoneVmExtensionPoliciesUpdateRequest',
        'ComputeOrganizationZoneVmExtensionPoliciesUpdateRequest',
        vmExtensionPolicy=self._name,
        vmExtensionPolicyResource=policy,
    )

  def Delete(self) -> Sequence[Any]:
    """Deletes the policy."""
    return self._MakeRequest(
        'Delete',
        'ComputeZoneVmExtensionPoliciesDeleteRequest',
        'ComputeFolderZoneVmExtensionPoliciesDeleteRequest',
        'ComputeOrganizationZoneVmExtensionPoliciesDeleteRequest',
        vmExtensionPolicy=self._name,
    )

  def Describe(self) -> Sequence[Any]:
    """Returns the policy."""
    return self._MakeRequest(
        'Get',
        'ComputeZoneVmExtensionPoliciesGetRequest',
        'ComputeFolderZoneVmExtensionPoliciesGetRequest',
        'ComputeOrganizationZoneVmExtensionPoliciesGetRequest',
        vmExtensionPolicy=self._name,
    )

  def List(self) -> Sequence[Any]:
    """Returns the policies of the zone."""
    return self._MakeRequest(
        'List',
        'ComputeZoneVmExtensionPoliciesListRequest',
        'ComputeFolderZoneVmExtensionPoliciesListRequest',
        'ComputeOrganizationZoneVmExtensionPoliciesListRequest',
    )

  def DescribeExtension(self) -> Sequence[Any]:
    """Returns the VM extension named by this client."""
    return self._MakeRequest(
        'GetVmExtension',
        'ComputeZoneVmExtensionPoliciesGetVmExtensionRequest',
        'ComputeFolderZoneVmExtensionPoliciesGetVmExtensionRequest',
        'ComputeOrganizationZoneVmExtensionPoliciesGetVmExtensionRequest',
        extensionName=self._name,
    )

  def ListExtensions(self) -> Sequence[Any]:
    """Returns the VM extensions available in the zone."""
    return self._MakeRequest(
        'ListVmExtensions',
        'ComputeZoneVmExtensionPoliciesListVmExtensionsRequest',
        'ComputeFolderZoneVmExtensionPoliciesListVmExtensionsRequest',
        'ComputeOrganizationZoneVmExtensionPoliciesListVmExtensionsRequest',
    )
