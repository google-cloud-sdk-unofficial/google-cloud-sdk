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
"""Contains the properties for the 'metrics' section."""

from googlecloudsdk.core.properties.providers import PROVIDERS
from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import _UserAgentHeaderValueValidator


class _SectionMetrics(_Section):
  """Contains the properties for the 'metrics' section."""

  def __init__(self):
    super(_SectionMetrics, self).__init__('metrics', hidden=True)
    self.environment = self._Add(
        'environment',
        validator=_UserAgentHeaderValueValidator,
        hidden=True,
    )
    self.environment_version = self._Add('environment_version', hidden=True)
    self.command_name = self._Add('command_name', internal=True)

    self.agent_name = self._Add(
        'agent_name', hidden=True, callbacks=[PROVIDERS['GetAgentName']]
    )
    self.request_attribution = self._Add(
        'request_attribution',
        validator=_UserAgentHeaderValueValidator,
        help_text=(
            'Attribution string to include in the User-Agent header for'
            ' requests made by gcloud.'
        ),
        hidden=True,
    )
