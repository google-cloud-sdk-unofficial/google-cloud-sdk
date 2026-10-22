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
"""Contains the properties for the 'memcache' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionMemcache(_Section):
  """Contains the properties for the 'memcache' section."""

  def __init__(self):
    super(_SectionMemcache, self).__init__('memcache')
    self.region = self._Add(
        'region',
        help_text=(
            'Default region to use when working with Cloud Memorystore for'
            ' Memcached resources. When a `region` is required but not provided'
            ' by a flag, the command will fall back to this value, if set.'
        ),
    )
