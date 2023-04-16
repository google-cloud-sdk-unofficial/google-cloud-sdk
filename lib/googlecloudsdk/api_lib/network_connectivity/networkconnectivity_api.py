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
"""Commands for interacting with the Network Connectivity API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_util
from googlecloudsdk.calliope import base


class SpokesClient(object):
  """Client for spoke service in network connectivity API."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    self.release_track = release_track
    self.client = networkconnectivity_util.GetClientInstance(release_track)
    self.messages = networkconnectivity_util.GetMessagesModule(release_track)
    self.spoke_service = self.client.projects_locations_spokes
    self.operation_service = self.client.projects_locations_operations

  def Activate(self, spoke_ref):
    """Call API to activate an existing spoke."""
    activate_req = (
        self.messages.NetworkconnectivityProjectsLocationsSpokesActivateRequest(
            name=spoke_ref.RelativeName()))
    return self.spoke_service.Activate(activate_req)

  def Deactivate(self, spoke_ref):
    """Call API to deactivate an existing spoke."""
    deactivate_req = (
        self.messages
        .NetworkconnectivityProjectsLocationsSpokesDeactivateRequest(
            name=spoke_ref.RelativeName()))
    return self.spoke_service.Deactivate(deactivate_req)

  def Accept(self, spoke_ref):
    """Call API to activate an existing spoke."""
    accept_req = (
        self.messages.NetworkconnectivityProjectsLocationsSpokesAcceptRequest(
            name=spoke_ref.RelativeName()))
    return self.spoke_service.Accept(accept_req)

  def Reject(self, spoke_ref, rejection_details):
    """Call API to reject an existing spoke."""
    rejection_detailed_req = self.messages.RejectSpokeRequest(
        details=rejection_details)
    reject_req = (
        self.messages
        .NetworkconnectivityProjectsLocationsSpokesRejectRequest(
            name=spoke_ref.RelativeName(),
            rejectSpokeRequest=rejection_detailed_req))
    return self.spoke_service.Reject(reject_req)

  def Delete(self, spoke_ref):
    """Call API to delete an existing spoke."""
    delete_req = (
        self.messages.NetworkconnectivityProjectsLocationsSpokesDeleteRequest(
            name=spoke_ref.RelativeName()))
    return self.spoke_service.Delete(delete_req)

  def Get(self, spoke_ref):
    """Call API to get an existing spoke."""
    get_req = (
        self.messages.NetworkconnectivityProjectsLocationsSpokesGetRequest(
            name=spoke_ref.RelativeName()))
    return self.spoke_service.Get(get_req)

  def List(self,
           region_ref,
           limit=None,
           filter_expression=None,
           order_by='',
           page_size=None,
           page_token=None):
    """Call API to list spokes."""
    list_req = (
        self.messages.NetworkconnectivityProjectsLocationsSpokesListRequest(
            parent=region_ref.RelativeName(),
            filter=filter_expression,
            orderBy=order_by,
            pageSize=page_size,
            pageToken=page_token))
    return list_pager.YieldFromList(
        self.spoke_service,
        list_req,
        field='spokes',
        limit=limit,
        batch_size_attribute='pageSize')

  def CreateVPCSpoke(self, spoke_ref, spoke, request_id=None):
    """Call API to create a new spoke."""
    parent = spoke_ref.Parent().RelativeName()
    spoke_id = spoke_ref.Name()

    create_req = (
        self.messages.NetworkconnectivityProjectsLocationsSpokesCreateRequest(
            parent=parent, requestId=request_id, spoke=spoke, spokeId=spoke_id))
    return self.spoke_service.Create(create_req)

  def UpdateVPCSpoke(self, spoke_ref, spoke, update_mask, request_id=None):
    """Call API to update a existing spoke."""
    name = spoke_ref.RelativeName()
    update_mask_string = ','.join(update_mask)

    update_req = (
        self.messages.NetworkconnectivityProjectsLocationsSpokesPatchRequest(
            name=name,
            requestId=request_id,
            spoke=spoke,
            updateMask=update_mask_string))
    return self.spoke_service.Patch(update_req)


class HubsClient(object):
  """Client for hub service in network connectivity API."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    self.release_track = release_track
    self.client = networkconnectivity_util.GetClientInstance(release_track)
    self.messages = networkconnectivity_util.GetMessagesModule(release_track)
    self.hub_service = self.client.projects_locations_global_hubs

  def ListHubSpokes(
      self,
      hub_ref,
      spoke_locations=None,
      limit=None,
      filter_expression=None,
      order_by='',
      # If page_size is set to None, ListHubSpokes will return all spokes
      # (defaults to 500). Accordingly, pagination will be handled on the client
      # side.
      page_size=None,
      page_token=None,
      view=None,
  ):
    """Call API to list spokes."""
    list_req = self.messages.NetworkconnectivityProjectsLocationsGlobalHubsListSpokesRequest(
        name=hub_ref.RelativeName(),
        spokeLocations=spoke_locations,
        filter=filter_expression,
        orderBy=order_by,
        pageSize=page_size,
        pageToken=page_token,
        view=view,
    )
    return list_pager.YieldFromList(
        self.hub_service,
        list_req,
        field='spokes',
        limit=limit,
        batch_size_attribute='pageSize',
        method='ListSpokes'
    )
