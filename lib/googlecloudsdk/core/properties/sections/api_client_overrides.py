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
"""Contains the properties for the 'api_client_overrides' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionApiClientOverrides(_Section):
  """Contains the properties for the 'api-client-overrides' section.

  This overrides the API client version to use when talking to this API.
  """

  def __init__(self):
    super(_SectionApiClientOverrides, self).__init__(
        'api_client_overrides', hidden=True
    )
    self.alloydb = self._Add('alloydb')
    self.appengine = self._Add('appengine')
    self.backupdr = self._Add('backupdr')
    self.baremetalsolution = self._Add('baremetalsolution')
    self.cloudidentity = self._Add('cloudidentity')
    self.compute = self._Add('compute')
    self.compute_alpha = self._Add('compute/alpha')
    self.compute_beta = self._Add('compute/beta')
    self.compute_v1 = self._Add('compute/v1')
    self.container = self._Add('container')
    self.speech = self._Add('speech')
    self.sql = self._Add('sql')
    self.storage = self._Add('storage')
    self.run = self._Add('run')
    self.scc = self._Add('securitycenter')
    self.cloudresourcemanager = self._Add('cloudresourcemanager')
    self.workstations = self._Add('workstations')
