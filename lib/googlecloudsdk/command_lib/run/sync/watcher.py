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
"""Base watcher for file changes to sync to Cloud Run."""

import abc
import os
import threading
from typing import Optional, Sequence, Set, Tuple

from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run.sync import sync_rule_util
from googlecloudsdk.command_lib.run.sync import syncer as syncer_lib
from googlecloudsdk.command_lib.util import gcloudignore

_DEFAULT_DEBOUNCE_DELAY_SECONDS = 0.3


class FileChangeAggregator:
  """Aggregates file changes (creates, modifies, deletes) and manages state.

  This class is thread-safe.
  """

  def __init__(self):
    self._lock = threading.Lock()
    self._create_set = set()
    self._modify_set = set()
    self._delete_set = set()

  def AddCreated(self, abs_src_path: str):
    """Marks the file as created."""
    with self._lock:
      if abs_src_path in self._delete_set:
        # If file is re-created after deletion, we mark it as modified instead
        # of new file to ensure it updates the existing (previously deleted)
        # file.
        self._delete_set.remove(abs_src_path)
        self._modify_set.add(abs_src_path)
      else:
        self._create_set.add(abs_src_path)

  def AddModified(self, abs_src_path: str):
    """Marks the file as modified."""
    with self._lock:
      if abs_src_path not in self._create_set:
        self._modify_set.add(abs_src_path)
      if abs_src_path in self._delete_set:
        # This should not happen because deleted files should not be modified
        # before getting re-created. But if it happens, we just remove it from
        # delete set and add it to modify set.
        self._delete_set.remove(abs_src_path)

  def AddDeleted(self, abs_src_path: str):
    """Adds the file to delete."""
    with self._lock:
      if abs_src_path in self._create_set:
        # If created then deleted, we just forget about it.
        self._create_set.remove(abs_src_path)
      elif abs_src_path in self._modify_set:
        # If modified then deleted, we forget modification and mark for delete.
        self._modify_set.remove(abs_src_path)
        self._delete_set.add(abs_src_path)
      else:
        self._delete_set.add(abs_src_path)

  def PopChanges(self) -> Tuple[Set[str], Set[str]]:
    """Returns the aggregated changes and clears them.

    Returns:
      A tuple of (files_to_sync, files_to_delete).
      files_to_sync includes both created and modified files.
    """
    with self._lock:
      syncs = self._create_set.union(self._modify_set)
      deletes = self._delete_set.copy()

      self._create_set.clear()
      self._modify_set.clear()
      self._delete_set.clear()

      return syncs, deletes

  def RestoreChanges(self, syncs: Set[str], deletes: Set[str]):
    """Restores files that failed to sync.

    Only restores files if they haven't been modified or deleted again
    during the failed sync. Any previously tracked 'created' files will be
    restored as 'modified', which is safe because 'modified' works correctly
    for existing sync targets.

    Args:
      syncs: Set of files which failed to sync.
      deletes: Set of files which failed to delete.
    """
    with self._lock:
      for file in syncs:
        if (
            file not in self._create_set
            and file not in self._modify_set
            and file not in self._delete_set
        ):
          self._modify_set.add(file)
      for file in deletes:
        if (
            file not in self._create_set
            and file not in self._modify_set
            and file not in self._delete_set
        ):
          self._delete_set.add(file)


class BaseWatcher(abc.ABC):
  """Base class for file watchers."""

  def __init__(
      self,
      source_dir: str,
      sync_rules: Sequence[sync_rule_util.SyncRule],
      syncer: syncer_lib.BaseSyncer,
      debounce_delay_seconds: float = _DEFAULT_DEBOUNCE_DELAY_SECONDS,
  ):
    """Initialize the watcher."""
    self.abs_source_dir = os.path.abspath(source_dir)
    self.sync_rules = sync_rules
    self.syncer = syncer
    self._aggregator = FileChangeAggregator()
    self._file_chooser = gcloudignore.GetFileChooserForDir(
        self.abs_source_dir, write_on_disk=False
    )
    self._sync_lock = threading.Lock()

    if debounce_delay_seconds is None:
      raise ValueError('debounce_delay_seconds must be set')
    self._debounce_delay_seconds = debounce_delay_seconds
    self._debounce_lock = threading.Lock()
    self._debounce_timer: Optional[threading.Timer] = None

  def _IsIgnored(self, path: str, is_directory: bool = False) -> bool:
    """Return True if file is outside source_dir or ignored."""
    try:
      rel_path = os.path.relpath(path, self.abs_source_dir)
      if os.path.isabs(rel_path) or rel_path.startswith('..'):
        return True
      return not self._file_chooser.IsIncluded(rel_path, is_dir=is_directory)
    except ValueError:
      return True

  @abc.abstractmethod
  def Watch(self):
    """Start watching for changes."""

  def _ScheduleSync(self):
    """Triggers the sync callback after the debounce delay.

    If a trigger is already pending, it is rescheduled.
    """
    with self._debounce_lock:
      if self._debounce_timer:
        self._debounce_timer.cancel()
      self._debounce_timer = threading.Timer(
          self._debounce_delay_seconds, self._Sync
      )
      self._debounce_timer.start()

  def _CancelSync(self):
    """Cancels any pending trigger."""
    with self._debounce_lock:
      if self._debounce_timer:
        self._debounce_timer.cancel()
        self._debounce_timer = None

  def _Sync(self):
    """Performs the sync operation."""
    # Serialize sync operations to prevent race conditions.
    with self._sync_lock:
      syncs, deletes = self._aggregator.PopChanges()

      sync_map = {}
      for src_path in syncs:
        dest_paths = sync_rule_util.GetDestPaths(
            src_path, self.abs_source_dir, self.sync_rules
        )
        if dest_paths:
          sync_map[src_path] = dest_paths

      deleted_map = {}
      for src_path in deletes:
        dest_paths = sync_rule_util.GetDestPaths(
            src_path, self.abs_source_dir, self.sync_rules
        )
        if dest_paths:
          deleted_map[src_path] = dest_paths

      if sync_map or deleted_map:
        try:
          self.syncer.Sync(sync_map, deleted_map)
        except Exception as e:  # pylint: disable=broad-exception-caught
          self._aggregator.RestoreChanges(syncs, deletes)
          pretty_print.Info('Sync failed, will retry on next event: {e}', e=e)
