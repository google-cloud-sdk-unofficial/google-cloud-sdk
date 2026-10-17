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
"""Colorization helpers for compute instance groups commands."""

import os

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import property_actions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import encoding


def AddNoColorFlag(parser):
  """Adds the --no-color flag for disabling output colorization."""
  parser.add_argument(
      '--no-color',
      default=None,
      action=property_actions.StoreConstProperty(
          properties.VALUES.core.disable_color, True
      ),
      category=base.LIST_COMMAND_FLAGS,
      help='Disable colorization of the table output.',
  )


def Colorize(text, color):
  """Wraps text in a console_attr.Colorizer if colorized output is enabled.

  Colorization is skipped when the core/disable_color property or the NO_COLOR
  environment variable is set, or when stdout is not an interactive terminal.

  Args:
    text: The text to colorize.
    color: The color name (as understood by console_attr.Colorizer) or None.

  Returns:
    A console_attr.Colorizer, or the unchanged text if colorization is disabled
    or either text or color is empty.
  """
  if not text or not color:
    return text
  if properties.VALUES.core.disable_color.GetBool():
    return text
  if encoding.GetEncodedValue(os.environ, 'NO_COLOR'):
    return text
  if not console_io.IsInteractive(output=True):
    return text
  return console_attr.Colorizer(text, color)
