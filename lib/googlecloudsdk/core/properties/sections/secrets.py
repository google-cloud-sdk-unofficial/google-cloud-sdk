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
"""Contains the properties for the 'secrets' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionSecrets(_Section):
  """Contains the properties for the 'secrets' section."""

  def __init__(self):
    super(_SectionSecrets, self).__init__('secrets')
    self.replication_policy = self._Add(
        'replication-policy',
        choices=['automatic', 'user-managed'],
        help_text=(
            'The type of replication policy to apply to secrets. Allowed '
            'values are "automatic" and "user-managed". If user-managed then '
            'locations must also be provided.'
        ),
    )
    self.locations = self._Add(
        'locations',
        help_text=(
            'A comma separated list of the locations to replicate '
            'secrets to. Only applies to secrets with a user-managed policy.'
        ),
    )
