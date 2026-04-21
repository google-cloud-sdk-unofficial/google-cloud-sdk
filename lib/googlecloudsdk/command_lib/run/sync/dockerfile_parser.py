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
"""Parses Dockerfile and extracts logical lines."""

from googlecloudsdk.core.util import files

_SINGLE_QUOTE = "'"
_DOUBLE_QUOTE = '"'
_COMMENT_CHAR = '#'
_BACKSLASH = '\\'


def _RemoveComments(line: str) -> str:
  """Checks for # char outside of quotes and removes the comment."""
  escaped = False
  in_single_quotes = False
  in_double_quotes = False

  for i, char in enumerate(line):
    # Handle escape character (\)
    if char == _BACKSLASH and not escaped:
      escaped = True
    elif escaped:
      escaped = False
    else:
      # Not escaped
      if char == _DOUBLE_QUOTE and not in_single_quotes:
        in_double_quotes = not in_double_quotes
      elif char == _SINGLE_QUOTE and not in_double_quotes:
        in_single_quotes = not in_single_quotes
      elif (
          char == _COMMENT_CHAR
          and not in_double_quotes
          and not in_single_quotes
      ):
        # Check if it's the start of the line or preceded by whitespace
        if i == 0 or line[i - 1].isspace():
          return line[:i].strip()

  return line.strip()


def ReadDockerfile(dockerfile_path: str) -> list[str]:
  """Reads Dockerfile, removes comments, and handles line continuations.

  Args:
    dockerfile_path: The absolute path to the Dockerfile to read.

  Returns:
    A list of logical instruction lines from the Dockerfile.
  """
  logical_lines = []
  buffer = ''

  with files.FileReader(dockerfile_path) as file:
    for line in file:
      # 1. Remove comments from the line
      clean_line = _RemoveComments(line)

      # 2. Skip if the line became empty after removing comments/whitespace
      if not clean_line:
        continue

      # 3. Handle the backslash continuation character
      if clean_line.endswith('\\'):
        # Remove the backslash and add a space for the join
        buffer += clean_line[:-1].rstrip() + ' '
      else:
        # Finalize the instruction
        full_instruction = (buffer + clean_line).strip()
        logical_lines.append(full_instruction)
        buffer = ''

  # Catch trailing buffer if the file ends on a backslash
  if buffer:
    logical_lines.append(buffer.strip())

  return logical_lines
