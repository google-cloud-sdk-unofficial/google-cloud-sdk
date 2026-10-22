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
"""Contains the properties for the 'composer' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionComposer(_Section):
  """Contains the properties for the 'composer' section."""

  def __init__(self):
    super(_SectionComposer, self).__init__('composer')
    self.location = self._Add(
        'location',
        help_text=(
            'Composer location to use. Each Composer location '
            'constitutes an independent resource namespace constrained to '
            'deploying environments into Compute Engine regions inside this '
            'location. This parameter corresponds to the '
            '/locations/<location> segment of the Composer resource URIs being '
            'referenced.'
        ),
    )
