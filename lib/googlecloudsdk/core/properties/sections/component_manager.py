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
"""Contains the properties for the 'component_manager' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionComponentManager(_Section):
  """Contains the properties for the 'component_manager' section."""

  def __init__(self):
    super(_SectionComponentManager, self).__init__('component_manager')
    self.additional_repositories = self._Add(
        'additional_repositories',
        help_text=(
            'Comma separated list of additional repositories to check '
            'for components.  This property is automatically managed by the '
            '`gcloud components repositories` commands.'
        ),
    )
    self.disable_update_check = self._AddBool(
        'disable_update_check',
        help_text=(
            'If True, Google Cloud CLI will not automatically check for '
            'updates.'
        ),
    )
    self.disable_warning = self._AddBool(
        'disable_warning',
        hidden=True,
        help_text=(
            'If True, Google Cloud CLI will not display warning messages '
            'about overridden configurations.'
        ),
    )
    self.fixed_sdk_version = self._Add('fixed_sdk_version', hidden=True)
    self.snapshot_url = self._Add('snapshot_url', hidden=True)
    # We need the original snapshot_url because snapshot_url may be
    # overwritten by users. Without original_snapshot_url, users can be trapped
    # to the overwritten snapshot_url even after it is unset.
    self.original_snapshot_url = self._Add(
        'original_snapshot_url',
        internal=True,
        hidden=True,
        help_text='Snapshot URL when this installation is firstly installed.',
        default=(
            'https://dl.google.com/dl/cloudsdk/channels/rapid/components-2.json'
        ),
    )
