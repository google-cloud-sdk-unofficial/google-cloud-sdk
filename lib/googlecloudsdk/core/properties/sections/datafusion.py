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
"""Contains the properties for the 'datafusion' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionDatafusion(_Section):
  """Contains the properties for the 'datafusion' section."""

  def __init__(self):
    super(_SectionDatafusion, self).__init__('datafusion')
    self.location = self._Add(
        'location',
        help_text=(
            'Datafusion location to use. Each Datafusion location constitutes'
            ' an independent resource namespace constrained to deploying'
            ' environments into Compute Engine regions inside this location.'
            ' This parameter corresponds to the /locations/<location> segment'
            ' of the Datafusion resource URIs being referenced.'
        ),
    )
