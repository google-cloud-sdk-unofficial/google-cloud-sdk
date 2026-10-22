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
"""Contains the properties for the 'gcloudignore' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionGcloudignore(_Section):
  """Contains the properties for the 'gcloudignore' section."""

  def __init__(self):
    super(_SectionGcloudignore, self).__init__('gcloudignore')
    self.enabled = self._AddBool(
        'enabled',
        default=True,
        help_text=(
            'If True, do not upload `.gcloudignore` files (see `$ gcloud topic '
            'gcloudignore`). If False, turn off the gcloudignore mechanism '
            'entirely and upload all files.'
        ),
    )
