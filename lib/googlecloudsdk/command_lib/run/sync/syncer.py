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
"""Syncer for file changes to Cloud Run."""

import abc
import os
import posixpath
import shlex
import tarfile
import time
from typing import Mapping, Sequence

from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files


# Using `-p` ensures that the tarball is extracted with the permissions set
# by the syncer, this is important for files that are not owned by root created
# by buildpacks.
_TAR_EXTRACT_COMMAND = ['tar', '-xpf', '-', '-C', '/']

# Using `-f` ensures that the container's `rm` silently returns success if
# the target file is already gone.
# This will avoid sync error loop trying to delete the file.
_RM_COMMAND = ['rm', '-rf', '--']
_DELETE_BATCH_SIZE = 100  # Max number of files to delete in a single command.


class SyncError(exceptions.Error):
  """Error raised when syncing files fails."""


class BaseSyncer(abc.ABC):
  """Base class for syncers."""

  def __init__(self, deployment_name, is_buildpack: bool):
    self.deployment_name = deployment_name
    self._permission_filter = (
        _BuildpackCompatibleFilter if is_buildpack else None
    )

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    pass

  @abc.abstractmethod
  def _CopyFiles(self, sync_map):
    """Copies files to the container.

    Args:
      sync_map: map of source file location to destination files location which
        needs to be synced.
    """
    pass

  @abc.abstractmethod
  def _DeleteFiles(self, deleted_map):
    """Deletes files from the container.

    Args:
      deleted_map: map of source file location to destination files location
        which needs to be deleted.
    """
    pass

  @classmethod
  def _GetTracker(cls, message):
    """Gets the progress tracker for the sync command."""
    return progress_tracker.ProgressTracker(message)

  def Sync(
      self,
      sync_map: Mapping[str, Sequence[str]],
      deleted_map: Mapping[str, Sequence[str]],
  ):
    """Sync changes to the container.

    Args:
      sync_map: map of source file location to destination files location which
        needs to be synced.
      deleted_map: map of source file location to destination files location
        which needs to be deleted.
    """
    if not sync_map and not deleted_map:
      return

    start_time = time.time()
    if deleted_map:
      filenames = ', '.join([os.path.basename(f) for f in deleted_map.keys()])
      with self._GetTracker(
          f'Deleting from "{self.deployment_name}": {filenames}'
      ):
        self._DeleteFiles(deleted_map)

    if sync_map:
      filenames = ', '.join([os.path.basename(f) for f in sync_map.keys()])
      with self._GetTracker(
          f'Syncing to "{self.deployment_name}": {filenames}'
      ):
        self._CopyFiles(sync_map)

    log.debug(
        '%s finished syncing in %s seconds',
        self.__class__.__name__,
        time.time() - start_time,
    )

  def _CreateTarball(self, sync_map, tar_contents):
    """Creates a tarball of the files to copy.

    Args:
      sync_map: map of source file location to destination files location which
        needs to be synced.
      tar_contents: file object to write the tarball to.
    """
    with tarfile.open(fileobj=tar_contents, mode='w') as tar:
      for abs_src_path, abs_dest_paths in sync_map.items():
        for abs_dest_path in abs_dest_paths:
          if not posixpath.isabs(abs_dest_path):
            raise ValueError(
                f'Cannot sync file: "{abs_src_path}". Destination paths must be'
                f' absolute. Found: {abs_dest_path}.'
            )
          try:
            # recusrsive=False as we expect abs_src_path to be a file and not a
            # folder. If file is swapped with a folder between detection and
            # sync, this will help avoid syncing the folder without detecting
            # it through watcher.
            tar.add(
                abs_src_path,
                arcname=abs_dest_path,
                recursive=False,
                filter=self._permission_filter,
            )
          except OSError as e:
            # Catching OSError (e.g., FileNotFoundError) handles the race
            # condition where a file is rapidly deleted or moved after the
            # watcher detects a modification, but before we can add it to the
            # synchronization tarball. Skipping it prevents thread crashes;
            # subsequent deletion events will be caught and handled
            # asynchronously by the watcher.
            log.warning(
                'Skipped adding file to tarball %s: %s', abs_src_path, e
            )
            pretty_print.Info(
                '{bold}WARNING:{reset} Skipped syncing "{abs_src_path}"'
                ' due to error: {e}',
                abs_src_path=abs_src_path,
                e=e,
            )
    log.debug('Tarball created')


class CloudRunSyncer(BaseSyncer):
  """Syncer for syncing files to a Cloud Run."""

  def __init__(
      self,
      deployment_name: str,
      is_buildpack: bool,
      ssh_session,
  ):
    super().__init__(deployment_name, is_buildpack)
    self._ssh_session = ssh_session

  def _CopyFiles(self, sync_map):
    """Copies files to the container."""
    with files.TemporaryDirectory() as tmp_dir:
      tar_path = os.path.join(tmp_dir, 'dev_sync_files.tar')
      with files.BinaryFileWriter(tar_path) as f:
        self._CreateTarball(sync_map, f)
      with files.BinaryFileReader(tar_path) as f:
        self._ssh_session.ExecuteCommand(_TAR_EXTRACT_COMMAND, input_data=f)

  def _DeleteFiles(self, deleted_map):
    """Deletes files from the container."""
    dests_to_delete = []
    for abs_src_path, abs_dest_paths in deleted_map.items():
      for abs_dest_path in abs_dest_paths:
        if not posixpath.isabs(abs_dest_path):
          raise ValueError(
              f'Cannot delete file for: "{abs_src_path}". Destination paths'
              f' must be absolute. Found: {abs_dest_path}.'
          )
      dests_to_delete.extend(abs_dest_paths)

    for i in range(0, len(dests_to_delete), _DELETE_BATCH_SIZE):
      batch = dests_to_delete[i : i + _DELETE_BATCH_SIZE]
      # Quote the files to prevent shell injection.
      quoted_batch = [shlex.quote(f) for f in batch]
      command = _RM_COMMAND + quoted_batch
      self._ssh_session.ExecuteCommand(command)


def _BuildpackCompatibleFilter(tarinfo: tarfile.TarInfo):
  """Sets correct permissions and ownership for files in the tarball.

  In Buildpack deployment the files are owned by webserver user and have 755
  permissions. When syncing the files we need to match those permissions.
  Webserver user is dynamic so we replace the ownership with root and set
  the same permissions.

  Args:
    tarinfo: tarinfo object to modify.

  Returns:
    A tarinfo object with buildpack compatible permissions.
  """

  tarinfo.uid = tarinfo.gid = 0
  tarinfo.uname = tarinfo.gname = 'root'
  tarinfo.mode = 0o755
  return tarinfo
