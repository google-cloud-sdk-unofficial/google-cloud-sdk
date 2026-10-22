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
"""Contains the properties for the 'devshell' section."""

from googlecloudsdk.core.docker import constants as const_lib
from googlecloudsdk.core.properties.types import _Section


class _SectionDevshell(_Section):
  """Contains the properties for the 'devshell' section."""

  def __init__(self):
    super(_SectionDevshell, self).__init__('devshell')
    self.image = self._Add(
        'image', hidden=True, default=const_lib.DEFAULT_DEVSHELL_IMAGE
    )
    self.metadata_image = self._Add(
        'metadata_image', hidden=True, default=const_lib.METADATA_IMAGE
    )
