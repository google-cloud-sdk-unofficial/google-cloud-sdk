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
"""Contains the properties for the 'deployment_manager' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionDeploymentManager(_Section):
  """Contains the properties for the 'deployment_manager' section."""

  def __init__(self):
    super(_SectionDeploymentManager, self).__init__('deployment_manager')
    self.glob_imports = self._AddBool(
        'glob_imports',
        default=False,
        help_text=(
            'Enable import path globbing. Uses glob patterns to match multiple '
            'imports in a config file.'
        ),
    )
