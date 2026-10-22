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
"""Contains the properties for the 'interactive' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionInteractive(_Section):
  """Contains the properties for the 'interactive' section."""

  def __init__(self):
    super(_SectionInteractive, self).__init__('interactive')
    self.bottom_bindings_line = self._AddBool(
        'bottom_bindings_line',
        default=True,
        help_text='If True, display the bottom key bindings line.',
    )
    self.bottom_status_line = self._AddBool(
        'bottom_status_line',
        default=False,
        help_text='If True, display the bottom status line.',
    )
    self.completion_menu_lines = self._Add(
        'completion_menu_lines',
        default=4,
        help_text='Number of lines in the completion menu.',
    )
    self.context = self._Add(
        'context', default='', help_text='Command context string.'
    )
    self.debug = self._AddBool(
        'debug',
        default=False,
        hidden=True,
        help_text='If True, enable the debugging display.',
    )
    self.fixed_prompt_position = self._Add(
        'fixed_prompt_position',
        default=False,
        help_text='If True, display the prompt at the same position.',
    )
    self.help_lines = self._Add(
        'help_lines',
        default=10,
        help_text='Maximum number of help snippet lines.',
    )
    self.hidden = self._AddBool(
        'hidden',
        default=False,
        help_text='If True, expose hidden commands/flags.',
    )
    self.justify_bottom_lines = self._AddBool(
        'justify_bottom_lines',
        default=False,
        help_text='If True, left- and right-justify bottom toolbar lines.',
    )
    self.manpage_generator = self._Add(
        'manpage_generator',
        default=True,
        help_text=(
            'If True, use the manpage CLI tree generator for '
            'unsupported commands.'
        ),
    )
    self.multi_column_completion_menu = self._AddBool(
        'multi_column_completion_menu',
        default=False,
        help_text='If True, display the completions as a multi-column menu.',
    )
    self.obfuscate = self._AddBool(
        'obfuscate',
        default=False,
        hidden=True,
        help_text='If True, obfuscate status PII.',
    )
    self.prompt = self._Add(
        'prompt', default='$ ', help_text='Command prompt string.'
    )
    self.show_help = self._AddBool(
        'show_help',
        default=True,
        help_text='If True, show help as command args are being entered.',
    )
    self.suggest = self._AddBool(
        'suggest',
        default=False,
        help_text='If True, add command line suggestions based on history.',
    )
