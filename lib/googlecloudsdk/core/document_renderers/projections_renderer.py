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

"""Cloud SDK markdown document projection keys renderer."""

import io

from googlecloudsdk.core.document_renderers import text_renderer


class ProjectionsRenderer(text_renderer.TextRenderer):
  """Renders only the PROJECTION KEYS section of a markdown document."""

  def __init__(self, *args, **kwargs):
    kwargs.setdefault('excluded_sections', ())
    super(ProjectionsRenderer, self).__init__(*args, **kwargs)
    self._file_out = self._out  # the output file inherited from TextRenderer
    self._null_out = io.StringIO()
    self._out = self._null_out
    self._has_projections = False

  def _CaptureOutput(self):
    if self._out == self._null_out:
      self._Flush()
    self._has_projections = True
    self._out = self._file_out

  def _DiscardOutput(self):
    if self._out == self._file_out:
      self._Flush()
    self._out = self._null_out

  def Heading(self, level, heading):
    if heading.strip() == 'PROJECTION KEYS':
      self._CaptureOutput()
    elif level <= 2:
      self._DiscardOutput()
    super(ProjectionsRenderer, self).Heading(level, heading)

  def Finish(self):
    if self._has_projections:
      self._out = self._file_out
      return super(ProjectionsRenderer, self).Finish()
    self._file_out.write(
        'No static projection schema available for this command.\n'
    )
    return None
