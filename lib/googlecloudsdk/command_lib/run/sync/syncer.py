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
import argparse
import os
import posixpath
import shlex
import subprocess
import tarfile
import time
from typing import Mapping, Sequence

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files


_TAR_EXTRACT_COMMAND = ['tar', '-xf', '-', '-C', '/']
_RM_COMMAND = ['rm', '-r', '--']
_DELETE_BATCH_SIZE = 100  # Max number of files to delete in a single command.


class SyncError(exceptions.Error):
  """Error raised when syncing files fails."""


class BaseSyncer(abc.ABC):
  """Base class for syncers."""

  def __init__(self, deployment_name):
    self.deployment_name = deployment_name

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
    if sync_map:
      filenames = ', '.join([os.path.basename(f) for f in sync_map.keys()])
      with self._GetTracker(
          f'Syncing to "{self.deployment_name}": {filenames}'
      ):
        self._CopyFiles(sync_map)

    if deleted_map:
      filenames = ', '.join([os.path.basename(f) for f in deleted_map.keys()])
      with self._GetTracker(
          f'Deleting from "{self.deployment_name}": {filenames}'
      ):
        self._DeleteFiles(deleted_map)

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
          tar.add(abs_src_path, arcname=abs_dest_path)
    log.debug('Tarball created')


class CloudRunSyncer(BaseSyncer):
  """Syncer for syncing files to a Cloud Run."""

  def __init__(
      self,
      args: argparse.Namespace,
      workload_type: run_ssh.Ssh.WorkloadType,
      tracker,
  ):
    super().__init__(args.deployment_name)

    tracker.StartStage(stages.FETCH_PROJECT_DETAILS)
    self._ssh = run_ssh.Ssh(args, workload_type)
    tracker.CompleteStage(stages.FETCH_PROJECT_DETAILS)
    self._cached_ssh_command_components = None
    self._control_path = None

  def PrimeSshConnection(self):
    """Creates a connection to the Cloud Run Instance.

    This can be called once at the start of sync to prime the SSH connection to
    reduce latency when syncing files.
    """
    self._SshAndExecuteCommand(['true'])

  def CloseMultiplexedSshConnection(self):
    """Closes the SSH connection."""
    if not self._control_path:
      # No connection has been established yet which uses multiplexing.
      return

    ssh_command = self._GetSshCommand(
        remote_command=None, extra_flags=['-O', 'exit']
    ).Build(ssh.Environment.Current())

    try:
      subprocess.run(ssh_command, check=False, capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
      log.warning('Timed out waiting for SSH master connection to close.')

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.CloseMultiplexedSshConnection()

  def _CopyFiles(self, sync_map):
    """Copies files to the container."""
    with files.TemporaryDirectory() as tmp_dir:
      tar_path = os.path.join(tmp_dir, 'dev_sync_files.tar')
      with files.BinaryFileWriter(tar_path) as f:
        self._CreateTarball(sync_map, f)
      with files.BinaryFileReader(tar_path) as f:
        self._SshAndExecuteCommand(_TAR_EXTRACT_COMMAND, input_data=f)

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
      self._SshAndExecuteCommand(command)

  def _SshAndExecuteCommand(self, remote_command, input_data=None):
    """Executes a command in the Cloud Run Instance container via SSH."""
    cmd = self._GetSshCommand(remote_command).Build(ssh.Environment.Current())

    result = subprocess.run(
        cmd, stdin=input_data, capture_output=True, check=False
    )

    if result.returncode != 0:
      stderr = encoding.Decode(result.stderr)
      # SSH returns 255 on connection errors (e.g., authentication failure).
      if result.returncode == 255:
        log.error('SSH connection failed: %s', stderr)
      else:
        log.error(
            'Remote command "%s" failed: %s', ' '.join(remote_command), stderr
        )
      # Re-raise the error so that the caller can handle it, but with the
      # decoded stderr and potentially better context.
      raise SyncError(
          f'Remote command {" ".join(remote_command)} failed: {stderr}'
      )

  def _GetSshMultiplexingOptions(self):
    """Gets SSH Multiplexing options.

    These options are used to keep the SSH connection alive for subsequent
    calls.

    Returns:
      A dictionary containing SSH options for connection multiplexing.
    """
    if not self._control_path:
      # Use a directory in ~/.ssh/ as it's standard and usually short enough.
      socket_dir = os.path.join(files.ExpandHomeDir('~/.ssh'), 'g_sync')
      files.MakeDir(socket_dir, mode=0o700)

      # Control path should be less than 104-108 characters due to Unix domain
      # sockets having a path length limitation. The `%C` token expands to a
      # string of around 40 characters. With a typical home directory path, the
      # total control path length is estimated to be around 80-100 characters,
      # staying within the limit.
      self._control_path = os.path.join(socket_dir, '%C')

    return {
        'ControlMaster': 'auto',
        'ControlPersist': '10m',
        'ControlPath': self._control_path,
    }

  def _GetSshCommand(self, remote_command, extra_flags=None):
    if self._cached_ssh_command_components:
      components = self._cached_ssh_command_components
    else:
      components = self._ssh.GetSshCommandComponents()
      self._cached_ssh_command_components = components

    ssh_options = components.options
    ssh_options.update(self._GetSshMultiplexingOptions())

    return run_ssh.ssh.SSHCommand(
        remote=components.remote,
        cert_file=components.cert_file,
        iap_tunnel_args=components.iap_tunnel_args,
        options=ssh_options,
        identity_file=components.identity_file,
        remote_command=remote_command,
        extra_flags=extra_flags,
    )
