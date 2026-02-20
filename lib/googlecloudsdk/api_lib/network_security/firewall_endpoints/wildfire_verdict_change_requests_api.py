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
"""API wrapper for `gcloud network-security firewall-endpoints` commands."""

import datetime

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


_API_VERSION_FOR_TRACK = {
    base.ReleaseTrack.ALPHA: 'v1alpha1',
}
ORG_OPERATIONS_COLLECTION = 'networksecurity.organizations.locations.operations'


class Client(object):
  """API client for firewall endpoints commands."""

  def __init__(self, release_track=base.ReleaseTrack.ALPHA):
    self.api_version = _API_VERSION_FOR_TRACK.get(release_track)
    self._client = apis.GetClientInstance('networksecurity', self.api_version)
    self.messages = self._client.MESSAGES_MODULE
    self._service = (
        self._client.organizations_locations_firewallEndpoints_wildfireVerdictChangeRequests
    )
    self._operations_client = self._client.organizations_locations_operations
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName('networksecurity', self.api_version)

  def CreateVerdictChangeRequest(self, parent, hash_val, verdict, comment):
    """Calls the Create Verdict Change Request API."""
    new_verdict_enum = (
        self.messages.WildfireVerdictChangeRequest.NewVerdictValueValuesEnum(
            verdict.upper()
        )
    )
    verdict_change_request = self.messages.WildfireVerdictChangeRequest(
        sha256=hash_val,
        newVerdict=new_verdict_enum,
        comment=comment,
    )
    request = self.messages.NetworksecurityOrganizationsLocationsFirewallEndpointsWildfireVerdictChangeRequestsCreateRequest(
        parent=parent,
        wildfireVerdictChangeRequest=verdict_change_request,
    )
    return self._service.Create(request)

  def ListVerdictChangeRequests(
      self, parent, limit=None, page_size=None
  ):
    """Calls the List Verdict Change Requests API."""
    list_request = self.messages.NetworksecurityOrganizationsLocationsFirewallEndpointsWildfireVerdictChangeRequestsListRequest(
        parent=parent,
    )
    return list_pager.YieldFromList(
        self._service,
        list_request,
        batch_size=page_size,
        limit=limit,
        field='wildfireVerdictChangeRequests',
        batch_size_attribute='pageSize',
    )

  def GetOperationsRef(self, operation):
    """Operations to Resource used for `waiter.WaitFor`."""
    return self._resource_parser.ParseRelativeName(
        operation.name,
        ORG_OPERATIONS_COLLECTION,
        False,
        self.api_version,
    )

  def WaitForOperation(
      self,
      operation_ref,
      message,
      has_result=False,
      max_wait=datetime.timedelta(seconds=600),
  ):
    """Waits for an operation to complete."""
    if has_result:
      poller = waiter.CloudOperationPoller(
          self._service, self._operations_client
      )
    else:
      poller = waiter.CloudOperationPollerNoResources(self._operations_client)

    response = waiter.WaitFor(
        poller, operation_ref, message, max_wait_ms=max_wait.seconds * 1000
    )
    return response

  def GetVerdictChangeRequest(self, name):
    """Calls the Get Verdict Change Request API.

    Args:
      name: The resource name of the WildfireVerdictChangeRequest to retrieve.

    Returns:
      The WildfireVerdictChangeRequest resource.
    """
    request = self.messages.NetworksecurityOrganizationsLocationsFirewallEndpointsWildfireVerdictChangeRequestsGetRequest(
        name=name,
    )
    return self._service.Get(request)
