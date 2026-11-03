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
"""Contains the properties for the 'regional' section."""

from googlecloudsdk.core.properties.constants import regional
from googlecloudsdk.core.properties.types import _Section


class _SectionRegional(_Section):
  """Contains the properties for the 'regional' section."""

  def __init__(self):
    super(_SectionRegional, self).__init__('regional')
    self.endpoint_mode = self._Add(
        'endpoint_mode',
        choices=[
            regional.GLOBAL,
            regional.REGIONAL,
            regional.REGIONAL_PREFERRED,
        ],
        help_text="""\
        Specifies endpoint mode for a given command. Regional endpoints
        provide enhanced data residency and reliability by ensuring your
        request is handled entirely within the specified Google Cloud region.
        This differs from global endpoints, which may process parts of the
        request outside the target region.

        Benefits of Regional Endpoints:
        (1) Data Residency: Keeps data in-transit within the chosen region.
        (2) Improved Isolation: Reduces the risk of cross-region impact
        from outages.

        The choices are:
        *   `global` - (Default) Use global rather than regional endpoints.
        *   `regional` - Only use regional endpoints. An error will be raised
            if a regional endpoint is not available for a given command.
        *   `regional-preferred` - Use regional endpoints when available,
            otherwise use global endpoints. Recommended for most users.
        """,
    )
    self.endpoint_compatibility = self._Add(
        'endpoint_compatibility',
        choices=[regional.SUPPORTED, regional.REQUIRED],
        hidden=True,
        help_text=(
            'Hidden property set by @base.RegionalEndpoints[Supported|Required]'
            ' annotation that indicates the level of regional endpoint'
            ' compatibility for the command/group in question.'
        ),
    )
