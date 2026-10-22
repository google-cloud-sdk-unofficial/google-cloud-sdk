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
"""Contains the properties for the 'emulator' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionEmulator(_Section):
  """Contains the properties for the 'emulator' section.

  This is used to configure emulator properties for pubsub and datastore, such
  as host_port and data_dir.
  """

  def __init__(self):
    super(_SectionEmulator, self).__init__('emulator', hidden=True)
    self.datastore_data_dir = self._Add('datastore_data_dir')
    self.pubsub_data_dir = self._Add('pubsub_data_dir')
    self.datastore_host_port = self._Add(
        'datastore_host_port', default='localhost:8081'
    )
    self.pubsub_host_port = self._Add(
        'pubsub_host_port', default='localhost:8085'
    )
    self.bigtable_host_port = self._Add(
        'bigtable_host_port', default='localhost:8086'
    )
