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
"""SSH multiplexed session for Cloud Run dev sync."""

import argparse
import hashlib
import os
import subprocess

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms


class SshError(exceptions.Error):
  """Error raised when remote SSH command execution fails."""


class MultiplexedSshSession:
  """Manages a multiplexed OpenSSH session to a Cloud Run instance."""

  def __init__(
      self,
      args: argparse.Namespace,
      workload_type: run_ssh.Ssh.WorkloadType,
  ):
    self._ssh = run_ssh.Ssh(args, workload_type)
    self._cached_ssh_command_components = None
    self._control_path = None
    self._env = ssh.Environment.Current()

    if platforms.OperatingSystem.IsWindows():
      self._env = ssh.Environment(ssh.Suite.OPENSSH, None)

  @property
  def env(self):
    return self._env

  def PrimeConnection(self):
    """Creates a connection to the Cloud Run Instance.

    This can be called once at the start of sync to prime the SSH connection to
    reduce latency when syncing files.
    """
    self.ExecuteCommand(['true'])

  def Close(self):
    """Closes the multiplexed SSH master connection."""
    if not self._control_path:
      # No connection has been established yet which uses multiplexing.
      return

    ssh_command = self.GetSshCommand(
        remote_command=None, extra_flags=['-O', 'exit']
    ).Build(self._env)

    try:
      subprocess.run(ssh_command, check=False, capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
      log.warning('Timed out waiting for SSH master connection to close.')

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.Close()

  def _GetSshMultiplexingOptions(self):
    """Gets SSH Multiplexing options.

    These options are used to keep the SSH connection alive for subsequent
    calls.

    Returns:
      A dictionary containing SSH options for connection multiplexing.
    """
    # OpenSSH connection multiplexing (ControlMaster/ControlPath) is not
    # supported on native Windows (Win32-OpenSSH). Fall back to non-multiplexed
    # connections.
    if platforms.OperatingSystem.IsWindows():
      return {}

    if not self._control_path:
      # Use a directory in ~/.ssh/ as it's standard and usually short enough.
      socket_dir = os.path.join(files.ExpandHomeDir('~/.ssh'), 'g_sync')
      files.MakeDir(socket_dir, mode=0o700)

      # Construct a unique socket name per workload and process session to
      # prevent cross-service or cross-instance multiplexing collisions.
      # Control path must remain under 104-108 characters due to Unix domain
      # socket path length limits. Using a 16-character SHA-256 hash keeps the
      # total path length well within limits (typically 60-70 characters).
      workload_key = (
          f'{self._ssh.project}:{self._ssh.region}:{self._ssh.workload_type}:'
          f'{self._ssh.deployment_name}:{self._ssh.instance}:'
          f'{self._ssh.revision}:{self._ssh.container}:{os.getpid()}'
      )
      socket_name = hashlib.sha256(workload_key.encode('utf-8')).hexdigest()[
          :16
      ]
      self._control_path = os.path.join(socket_dir, socket_name)

    return {
        'ControlMaster': 'auto',
        'ControlPersist': '10m',
        'ControlPath': self._control_path,
    }

  def GetSshCommand(self, remote_command, extra_flags=None):
    """Gets an SSHCommand configured with multiplexing options."""
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

  def ExecuteCommand(self, remote_command, input_data=None):
    """Executes a command in the Cloud Run Instance container via SSH."""
    cmd = self.GetSshCommand(remote_command).Build(self._env)

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

      # Clear cache as the components can get stale and need to be refreshed.
      self._cached_ssh_command_components = None
      # Re-raise the error so that the caller can handle it, but with the
      # decoded stderr and potentially better context.
      raise SshError(
          f'Remote command {" ".join(remote_command)} failed: {stderr}'
      )
