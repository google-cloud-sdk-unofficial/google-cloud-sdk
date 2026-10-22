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
"""Contains the properties for the 'transfer' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionTransfer(_Section):
  """Contains the properties for the 'transfer' section."""

  def __init__(self):
    super(_SectionTransfer, self).__init__('transfer', hidden=True)
    self.no_async_polling_interval_ms = self._Add(
        'no_async_polling_interval_ms',
        default=3000,
        hidden=True,
        help_text=(
            'Frequency for polling a transfer operation to see if it is done.'
        ),
    )
