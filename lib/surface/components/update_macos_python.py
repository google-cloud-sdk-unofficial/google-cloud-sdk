# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""`gcloud components update-macos-python` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core.updater import python_manager


@base.Hidden
@base.UniverseCompatible
class UpdateMacosPython(base.Command):
  """Updates managed Python installation on macOS."""

  @staticmethod
  def Args(parser):
    # Note: this command doesn't define any flags, and new flags should not be
    # added here. This is because update_manager.Update() forms the command line
    # to invoke this command using the existing gcloud code, then shells out to
    # the command, which runs using the new gcloud code. If the old and new
    # versions of the command had different sets of flags, this could result in
    # an error when parsing arguments (this is especially problematic for
    # version downgrades; any new flags added to this command would potentially
    # be missing when downgrading to older gcloud versions).
    pass

  def Run(self, args):
    python_manager.PromptAndInstallPythonOnMac()
