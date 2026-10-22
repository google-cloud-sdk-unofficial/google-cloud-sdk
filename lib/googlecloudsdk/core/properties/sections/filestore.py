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
"""Contains the properties for the 'filestore' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionFilestore(_Section):
  """Contains the properties for the 'filestore' section."""

  def __init__(self):
    super(_SectionFilestore, self).__init__('filestore')
    self.location = self._Add(
        'location',
        help_text=(
            'Please use the `--location` flag or set the '
            'filestore/zone or filestore/region property.'
        ),
    )
    self.zone = self._Add(
        'zone',
        help_text=(
            'Default zone to use when working with Cloud Filestore '
            'zones. When a `--zone` flag is required but not '
            'provided, the command will fall back to this value, if set.'
        ),
    )
    self.region = self._Add(
        'region',
        help_text=(
            'Default region to use when working with Cloud Filestore '
            'regions. When a `--region` flag is required but not '
            'provided, the command will fall back to this value, if set.'
        ),
    )
