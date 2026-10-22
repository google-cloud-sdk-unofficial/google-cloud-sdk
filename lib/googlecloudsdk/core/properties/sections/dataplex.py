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
"""Contains the properties for the 'dataplex' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionDataplex(_Section):
  """Contains the properties for the 'dataplex' section."""

  def __init__(self):
    super(_SectionDataplex, self).__init__('dataplex')
    self.location = self._Add(
        'location',
        help_text=(
            'Dataplex location to use. When a `location` is required but not '
            'provided by a flag, the command will fall back to this value, if '
            'set.'
        ),
    )
    self.lake = self._Add(
        'lake',
        help_text=(
            'Dataplex lake to use. When a `lake` is required but not '
            'provided by a flag, the command will fall back to this value, if '
            'set.'
        ),
    )
    self.zone = self._Add(
        'zone',
        help_text=(
            'Dataplex zone to use. When a `zone` is required but not '
            'provided by a flag, the command will fall back to this value, if '
            'set.'
        ),
    )
    self.asset = self._Add(
        'asset',
        help_text=(
            'Dataplex asset to use. When an `asset` is required but not '
            'provided by a flag, the command will fall back to this value, if '
            'set.'
        ),
    )
