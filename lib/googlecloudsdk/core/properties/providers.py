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
"""Dynamic default and provider callbacks for properties."""

import os

from googlecloudsdk.core import config
from googlecloudsdk.core.util import agents


def GetRuntimeRoot():
  """Returns the runtime root path for App Engine."""
  sdk_root = config.Paths().sdk_root
  if sdk_root is None:
    return None
  return os.path.join(sdk_root, 'platform', 'ext-runtime')


def GetAgentName():
  """Detects and returns the active AI agent name."""
  return agents.DetectAIAgent()


def StorageRsyncFilesDirectory():
  """Returns the default directory path to intermediary files created by rsync."""
  return os.path.join(
      config.Paths().global_config_dir, 'surface_data', 'storage', 'rsync_files'
  )


def StorageSymlinkPlaceholderDirectory():
  """Returns the default directory path to temporary symlink placeholder files."""
  return os.path.join(
      config.Paths().global_config_dir,
      'surface_data',
      'storage',
      'symlink_placeholders',
  )


def StorageTrackerFilesDirectory():
  """Returns the default directory path to tracker files for resumable operations."""
  return os.path.join(
      config.Paths().global_config_dir,
      'surface_data',
      'storage',
      'tracker_files',
  )


PROVIDERS = {
    'GetRuntimeRoot': GetRuntimeRoot,
    'GetAgentName': GetAgentName,
    'StorageRsyncFilesDirectory': StorageRsyncFilesDirectory,
    'StorageSymlinkPlaceholderDirectory': StorageSymlinkPlaceholderDirectory,
    'StorageTrackerFilesDirectory': StorageTrackerFilesDirectory,
}
