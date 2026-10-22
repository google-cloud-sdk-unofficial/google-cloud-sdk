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
"""Contains the properties for the 'pubsub' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionPubsub(_Section):
  """Contains the properties for the 'pubsub' section."""

  def __init__(self):
    super(_SectionPubsub, self).__init__('pubsub')
    self.legacy_output = self._AddBool(
        'legacy_output',
        default=False,
        internal=True,
        hidden=True,
        help_text=(
            'Use the legacy output for beta pubsub commands. The legacy '
            'output from beta is being deprecated. This property will '
            'eventually be removed.'
        ),
    )
