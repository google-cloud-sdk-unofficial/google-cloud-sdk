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
"""Polling watcher for file changes to sync to Cloud Run."""

import os
import time
from typing import Sequence

from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run.sync import sync_rule_util
from googlecloudsdk.command_lib.run.sync import syncer as syncer_lib
from googlecloudsdk.command_lib.run.sync import watcher

_DEFAULT_POLLING_INTERVAL_SECONDS = 1


class PollingWatcher(watcher.BaseWatcher):
  """Watcher for file changes to sync to Cloud Run using polling."""

  def __init__(
      self,
      source_dir: str,
      sync_rules: Sequence[sync_rule_util.SyncRule],
      syncer: syncer_lib.BaseSyncer,
      polling_interval_seconds: float = _DEFAULT_POLLING_INTERVAL_SECONDS,
      debounce_delay_seconds: float = watcher._DEFAULT_DEBOUNCE_DELAY_SECONDS,
  ):
    super().__init__(source_dir, sync_rules, syncer, debounce_delay_seconds)
    self._polling_interval_seconds = polling_interval_seconds
    self._file_states = {}

  def _ScanSourceDirectory(self):
    """Scans the directory and returns a map of file paths to their modification times."""
    current_states = {}
    for root, dirs, files in os.walk(self.abs_source_dir):
      # Filter ignored directories in-place to prune the walk
      dirs[:] = [
          d
          for d in dirs
          if not self._IsIgnored(os.path.join(root, d), is_directory=True)
      ]

      for f in files:
        abs_path = os.path.join(root, f)
        if not self._IsIgnored(abs_path):
          try:
            stat_result = os.stat(abs_path)
            # Track both mtime and size to catch fast modifications or files
            # replaced with older versions (e.g. tar extraction or cp -p).
            current_states[abs_path] = (
                stat_result.st_mtime,
                stat_result.st_size,
            )
          except OSError:
            # Ignore files that were deleted or inaccessible during os.walk
            pass
    return current_states

  def _AggregateChanges(self, current_states):
    sync_required = False
    for path, path_stat in current_states.items():
      if path not in self._file_states:
        self._aggregator.AddCreated(path)
        sync_required = True
      elif path_stat != self._file_states[path]:
        self._aggregator.AddModified(path)
        sync_required = True

    for path in self._file_states:
      if path not in current_states:
        self._aggregator.AddDeleted(path)
        sync_required = True

    return sync_required

  def Watch(self):
    """Start watching for changes."""
    pretty_print.Info('Watching for changes in: {dir}', dir=self.abs_source_dir)

    # Load initial state
    self._file_states = self._ScanSourceDirectory()

    try:
      while True:
        time.sleep(self._polling_interval_seconds)
        current_states = self._ScanSourceDirectory()

        sync_required = self._AggregateChanges(current_states)

        self._file_states = current_states
        if sync_required:
          self._ScheduleSync()
    finally:
      self._CancelSync()
