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
"""Contains the properties for the 'resource_policy' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionResourcePolicy(_Section):
  """Contains the properties for the 'resource_policy' section."""

  def __init__(self):
    super(_SectionResourcePolicy, self).__init__('resource_policy', hidden=True)
    self.org_restriction_header = self._Add(
        'org_restriction_header',
        default=None,
        help_text=(
            'Default organization restriction header to use when working with'
            ' GCP resources. If set, the value must be in JSON format and must'
            ' contain a comma separated list of authorized GCP organization'
            ' IDs. The JSON must then be encoded by following the RFC 4648,'
            ' section 5, specifications. See'
            ' https://www.rfc-editor.org/rfc/rfc4648#section-5 for more'
            ' information about base 64 encoding. And visit'
            ' https://cloud.google.com/resource-manager/docs/organization-restrictions/overview'
            ' for more information about organization restrictions.'
        ),
    )
