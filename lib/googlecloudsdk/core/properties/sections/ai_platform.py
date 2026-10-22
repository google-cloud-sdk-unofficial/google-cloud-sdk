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
"""Contains the properties for the 'ai_platform' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionAiPlatform(_Section):
  """Contains the properties for the command group 'ai_platform' section."""

  def __init__(self):
    super(_SectionAiPlatform, self).__init__('ai_platform')
    self.region = self._Add(
        'region',
        help_text=(
            'Default region to use when working with AI Platform Training and'
            ' Prediction resources (currently for Prediction only). It is'
            ' ignored for training resources for now. The value should be'
            ' either `global` or one of the supported regions. When a'
            ' `--region` flag is required but not provided, the command will'
            ' fall back to this value, if set.'
        ),
    )
