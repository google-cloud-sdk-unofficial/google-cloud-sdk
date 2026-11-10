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
"""Commands for interacting with the Cloud NetApp Files Inventory API resource."""

from googlecloudsdk.api_lib.netapp import util as netapp_api_util
from googlecloudsdk.calliope import base


class InventoryClient(object):
  """Wrapper for working with Inventory in the Cloud NetApp Files API Client."""

  def __init__(self, release_track=base.ReleaseTrack.ALPHA):
    self.release_track = release_track
    if self.release_track == base.ReleaseTrack.ALPHA:
      self._adapter = AlphaInventoryAdapter()
    elif self.release_track == base.ReleaseTrack.BETA:
      self._adapter = BetaInventoryAdapter()
    else:
      raise ValueError(
          '[{}] is not a valid API version.'.format(
              netapp_api_util.VERSION_MAP[release_track]
          )
      )

  @property
  def client(self):
    return self._adapter.client

  @property
  def messages(self):
    return self._adapter.messages

  def Get(self, location_ref, inventory_view=None):
    """Gets an Inventory."""
    request = self.messages.NetappProjectsLocationsGetInventoryRequest(
        name=f'{location_ref.RelativeName()}/inventory',
        view=inventory_view,
    )
    return self.client.projects_locations.GetInventory(request)


class BetaInventoryAdapter(object):
  """Adapter for the Beta Cloud NetApp Files API for Inventory."""

  def __init__(self):
    self.release_track = base.ReleaseTrack.BETA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )


class AlphaInventoryAdapter(BetaInventoryAdapter):
  """Adapter for the Alpha Cloud NetApp Files API for Inventory."""

  def __init__(self):
    super(AlphaInventoryAdapter, self).__init__()
    self.release_track = base.ReleaseTrack.ALPHA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )
