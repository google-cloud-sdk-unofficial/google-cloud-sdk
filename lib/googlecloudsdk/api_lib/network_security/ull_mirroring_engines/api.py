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
"""API wrapper for `gcloud network-security ull-mirroring-engines` commands."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources

_API_VERSION_FOR_TRACK = {
    base.ReleaseTrack.ALPHA: 'v1alpha1',
}
_API_NAME = 'networksecurity'


def GetApiVersion(release_track):
  return _API_VERSION_FOR_TRACK.get(release_track)


def GetMessagesModule(release_track=base.ReleaseTrack.ALPHA):
  api_version = GetApiVersion(release_track)
  return apis.GetMessagesModule(_API_NAME, api_version)


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA):
  api_version = GetApiVersion(release_track)
  return apis.GetClientInstance(_API_NAME, api_version)


class Client:
  """API client for Ull Mirroring Engine commands.

  Attributes:
    messages: API messages class, The Ull Mirroring Engine messages.
  """

  def __init__(self, release_track):
    api_version = GetApiVersion(release_track)
    self._client = GetClientInstance(release_track)
    self.messages = GetMessagesModule(release_track)
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName(_API_NAME, api_version)
    self._ull_mirroring_engine_client = (
        self._client.projects_locations_ullMirroringEngines
    )

  def ListNetworks(
      self, engine_name, page_size=None, filter_expr=None, order_by=None
  ):
    """Calls the ListNetworks API.

    Args:
      engine_name: str, the name of the UllMirroringEngine.
      page_size: int, optional page size.
      filter_expr: str, optional filter.
      order_by: str, optional order by.

    Yields:
      ListNetworksForEngineResponse.Network items.
    """
    page_token = None
    while True:
      req_body = self.messages.ListNetworksForEngineRequest(
          pageSize=page_size,
          pageToken=page_token,
          filter=filter_expr,
          orderBy=order_by,
      )
      request = self.messages.NetworksecurityProjectsLocationsUllMirroringEnginesListNetworksRequest(
          name=engine_name, listNetworksForEngineRequest=req_body
      )

      response = self._ull_mirroring_engine_client.ListNetworks(request)

      for network in response.networks:
        yield network

      if not response.nextPageToken:
        break
      page_token = response.nextPageToken
