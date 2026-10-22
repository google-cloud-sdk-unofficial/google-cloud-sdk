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
"""Contains the properties for the 'scc' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionScc(_Section):
  """Contains the properties for the 'scc' section."""

  def __init__(self):
    super(_SectionScc, self).__init__('scc')
    self.organization = self._Add(
        'organization',
        help_text='Default organization `gcloud` should use for scc surface.',
    )
    self.parent = self._Add(
        'parent',
        help_text='Default parent `gcloud` should use for scc surface.',
    )
