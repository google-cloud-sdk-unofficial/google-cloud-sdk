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

"""Cloud SDK markdown document section filter."""

from typing import Any, IO, Iterable, List, Optional


class SectionFilterStream(object):
  """A file-like input stream wrapper that filters out markdown sections.

  Filters out top-level sections (level <= 2 headings) matching any name in
  `excluded_sections`, along with all subsections (level > 2) and content within
  those sections, until the next non-excluded top-level section is reached.
  """

  def __init__(
      self,
      fin: IO[str],
      excluded_sections: Iterable[str] = ('PROJECTION KEYS',),
  ) -> None:
    """Initializes the filter stream.

    Args:
      fin: The underlying markdown input stream (file-like object).
      excluded_sections: Iterable of section heading titles (case-insensitive)
        to filter out.
    """
    self._fin = fin
    self._excluded_sections = {s.strip().upper() for s in excluded_sections}
    self._in_excluded_section = False
    self._in_code_block = False
    self._buffer = ''

  def _check_heading(self, line: str) -> bool:
    """Checks if a line is a markdown heading and updates filter state.

    Args:
      line: The line to check.

    Returns:
      bool: True if the line was a heading, False otherwise.
    """
    if not line:
      return False

    # Check for fenced code block toggle
    stripped = line.strip()
    if stripped.startswith('```'):
      # Single-line code span like ```inline code``` with non-backtick text
      if len(stripped) > 5 and stripped.endswith('```') and stripped.strip('`'):
        return False
      self._in_code_block = not self._in_code_block
      return False

    if self._in_code_block:
      return False

    # Headings must start at column 0 with '#' or '='
    marker = line[0]
    if marker not in ('#', '='):
      return False

    i = 0
    while i < len(line) and line[i] == marker:
      i += 1

    if i >= len(line) or line[i] != ' ':
      return False

    level = i
    stripped_line = line.rstrip('\r\n')

    # Check for optional matching closing markers (e.g. '## HEADING ##')
    if stripped_line.endswith(marker):
      closing_start = stripped_line.rfind(' ')
      if closing_start > i and set(stripped_line[closing_start + 1 :]) == {
          marker
      }:
        heading_text = stripped_line[i + 1 : closing_start].strip()
      else:
        heading_text = stripped_line[i + 1 :].strip()
    else:
      heading_text = stripped_line[i + 1 :].strip()

    # Strip inline markdown formatting embellishments (*, _, `) from title
    heading_text = heading_text.strip('*_`')

    if level <= 2:
      if heading_text.upper() in self._excluded_sections:
        self._in_excluded_section = True
      else:
        self._in_excluded_section = False

    return True

  def readline(self, size: int = -1) -> str:
    """Reads the next non-filtered line from the stream.

    Args:
      size: Maximum number of characters to return.

    Returns:
      str: The next non-filtered line, or '' at EOF.
    """
    if self._buffer:
      if '\n' in self._buffer:
        newline_idx = self._buffer.index('\n') + 1
        line = self._buffer[:newline_idx]
        self._buffer = self._buffer[newline_idx:]
      else:
        line = self._buffer
        self._buffer = ''
      if 0 <= size < len(line):
        self._buffer = line[size:] + self._buffer
        return line[:size]
      return line

    while True:
      line = self._fin.readline()
      if not line:
        return ''

      self._check_heading(line)

      if not self._in_excluded_section:
        if 0 <= size < len(line):
          self._buffer = line[size:]
          return line[:size]
        return line

  def read(self, size: Optional[int] = -1) -> str:
    """Reads non-filtered content from the stream.

    Args:
      size: Maximum number of characters to return. If negative or omitted,
        reads until EOF.

    Returns:
      str: The filtered content.
    """
    if size is None or size < 0:
      chunks = []
      while True:
        line = self.readline()
        if not line:
          break
        chunks.append(line)
      return ''.join(chunks)

    chunks = []
    bytes_read = 0
    while bytes_read < size:
      chunk = self.readline(size - bytes_read)
      if not chunk:
        break
      chunks.append(chunk)
      bytes_read += len(chunk)
    return ''.join(chunks)

  def readlines(self, hint: int = -1) -> List[str]:
    """Reads all remaining non-filtered lines.

    Args:
      hint: Approximate character limit to read.

    Returns:
      list of str: The filtered lines.
    """
    lines = []
    total = 0
    while True:
      line = self.readline()
      if not line:
        break
      lines.append(line)
      total += len(line)
      if hint > 0 and total >= hint:
        break
    return lines

  def __iter__(self) -> 'SectionFilterStream':
    return self

  def __next__(self) -> str:
    line = self.readline()
    if not line:
      raise StopIteration
    return line

  def next(self) -> str:
    return self.__next__()

  def close(self) -> None:
    """Closes the underlying stream if close() is supported."""
    if hasattr(self._fin, 'close'):
      self._fin.close()

  def __enter__(self) -> 'SectionFilterStream':
    return self

  def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
    self.close()

  @property
  def closed(self) -> bool:
    return getattr(self._fin, 'closed', False)

  def readable(self) -> bool:
    return True

  def writable(self) -> bool:
    return False

  def seekable(self) -> bool:
    return False
