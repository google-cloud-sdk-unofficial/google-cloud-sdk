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
"""Contains the properties for the 'gkebackup' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionGkebackup(_Section):
  """Contains the properties for 'gkebackup' section."""

  def __init__(self):
    super(_SectionGkebackup, self).__init__('gkebackup')
    self.location = self._Add(
        'location',
        default='-',
        help_text=(
            'Default location to use when working with Backup for GKE Services '
            'resources. When a `--location` flag is required but not provided, '
            'the command will fall back to this value.'
        ),
    )
    self.backup_plan = self._Add(
        'backup_plan',
        default='-',
        help_text=(
            'Default backup plan ID to use when working with Backup for GKE '
            'Services resources. When a `--backup-plan` flag is required but '
            'not provided, the command will fall back to this value.'
        ),
    )
    self.backup = self._Add(
        'backup',
        default='-',
        help_text=(
            'Default backup ID to use when working with Backup for GKE '
            'Services resources. When a `--backup` flag is required but not '
            'provided, the command will fall back to this value.'
        ),
    )
    self.restore = self._Add(
        'restore_plan',
        default='-',
        help_text=(
            'Default restore plan ID to use when working with Backup for GKE '
            'Services resources. When a `--restore-plan` flag is required but '
            'not provided, the command will fall back to this value.'
        ),
    )
    self.restore = self._Add(
        'restore',
        default='-',
        help_text=(
            'Default restore ID to use when working with Backup for GKE '
            'Services resources. When a `--restore` flag is required but not '
            'provided, the command will fall back to this value.'
        ),
    )
