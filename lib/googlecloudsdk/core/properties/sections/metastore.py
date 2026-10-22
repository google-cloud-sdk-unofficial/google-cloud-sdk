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
"""Contains the properties for the 'metastore' section."""

import enum
import textwrap

from googlecloudsdk.core.properties.exceptions import InvalidValueError
from googlecloudsdk.core.properties.types import _Section


class _SectionMetastore(_Section):
  """Contains the properties for the 'metastore' section."""

  # pylint: disable=invalid-name
  class Tier(enum.Enum):
    developer = 1
    enterprise = 3

  def TierValidator(self, tier):
    if tier is None:
      return

    if tier not in [x.name for x in list(_SectionMetastore.Tier)]:
      raise InvalidValueError(
          'tier `{0}` must be one of: [developer, enterprise]'.format(tier)
      )

  def __init__(self):
    super(_SectionMetastore, self).__init__('metastore')
    self.location = self._Add(
        'location',
        help_text=(
            'Default location to use when working with Dataproc Metastore. When'
            ' a `location` is required but not provided by a flag, the command'
            ' will fall back to this value, if set.'
        ),
    )
    self.tier = self._Add(
        'tier',
        validator=self.TierValidator,
        help_text=textwrap.dedent("""\
        Default tier to use when creating Dataproc Metastore services.
        When a `tier` is required but not provided by a flag,
        the command will fall back to this value, if set.
        +
        Valid values are:
            *   `developer` - The developer tier provides limited scalability
            and no fault tolerance. Good for low-cost proof-of-concept.
            *   `enterprise` - The enterprise tier provides multi-zone high
            availability, and sufficient scalability for enterprise-level
            Dataproc Metastore workloads."""),
        choices=[x.name for x in list(_SectionMetastore.Tier)],
    )
