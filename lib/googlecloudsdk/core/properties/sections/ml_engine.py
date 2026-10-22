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
"""Contains the properties for the 'ml_engine' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionMlEngine(_Section):
  """Contains the properties for the 'ml_engine' section."""

  def __init__(self):
    super(_SectionMlEngine, self).__init__('ml_engine')
    self.polling_interval = self._Add(
        'polling_interval',
        default=60,
        help_text=(
            'Interval (in seconds) at which to poll logs from your '
            'Cloud ML Engine jobs. Note that making it much faster than '
            'the default (60) will quickly use all of your quota.'
        ),
    )
    self.local_python = self._Add(
        'local_python',
        default=None,
        help_text=(
            'Full path to the Python interpreter to use for '
            'Cloud ML Engine local predict/train jobs. If not '
            'specified, the default path is the one to the Python '
            'interpreter found on system `PATH`.'
        ),
    )
