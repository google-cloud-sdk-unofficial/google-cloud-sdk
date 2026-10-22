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
"""Contains the properties for the 'netapp' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionNetapp(_Section):
  """Contains the properties for the 'netapp' section."""

  def __init__(self):
    super(_SectionNetapp, self).__init__('netapp')

    self.location = self._Add(
        'location',
        help_text=(
            'Default location to use when working with Cloud NetApp Files'
            ' resources. When a `location` value is required but not '
            'provided, the command will fall back to this value, if set.'
        ),
    )
