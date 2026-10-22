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
"""Contains the properties for the 'test' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionTest(_Section):
  """Contains the properties for the 'test' section."""

  def __init__(self):
    super(_SectionTest, self).__init__('test')
    self.results_base_url = self._Add('results_base_url', hidden=True)
    self.matrix_status_interval = self._Add(
        'matrix_status_interval', hidden=True
    )
