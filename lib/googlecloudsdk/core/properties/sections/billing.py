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
"""Contains the properties for the 'billing' section."""

import textwrap

from googlecloudsdk.core.properties.types import _Section


class _SectionBilling(_Section):
  """Contains the properties for the 'auth' section."""

  LEGACY = 'LEGACY'
  CURRENT_PROJECT = 'CURRENT_PROJECT'
  CURRENT_PROJECT_WITH_FALLBACK = 'CURRENT_PROJECT_WITH_FALLBACK'

  def __init__(self):
    super(_SectionBilling, self).__init__('billing')

    self.quota_project = self._Add(
        'quota_project',
        default=_SectionBilling.CURRENT_PROJECT,
        help_text=textwrap.dedent("""\
             The Google Cloud project that is billed and charged quota for
             operations performed in `gcloud`. When unset, the default is
             [CURRENT_PROJECT]. This default bills and charges quota against the
             current project. If you need to operate on one project, but need to
             bill your usage against or use quota from a different project, you
             can use this flag to specify the billing project. If both
             `billing/quota_project` and `--billing-project` are specified,
             `--billing-project` takes precedence.
             """),
    )
