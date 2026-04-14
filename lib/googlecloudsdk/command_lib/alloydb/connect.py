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
"""Helper functions for connecting to AlloyDB instances."""

import contextlib
import os
import platform
import subprocess
import tempfile
import time

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files


AUTH_PROXY_BINARY = 'alloydb-auth-proxy'
PSQL_BINARY = 'psql'


class PsqlNotFound(exceptions.Error):
  """Raise when the psql binary was not found on the PATH."""

  def __init__(self):
    msg = (
        'The psql binary is required for the connect command but was not'
        ' found in your environment. Please install psql and try again.'
    )
    super().__init__(msg)


class AuthProxyNotFound(exceptions.Error):
  """Raise when the Auth Proxy binary was not found on the PATH."""

  def __init__(self, system, machine):
    error = (
        'The AlloyDB Auth Proxy binary is required for the connect'
        ' command but was not found in your environment. '
    )
    action = 'Please install the AlloyDB Auth Proxy and try again.\n\n'
    learn_more = (
        'To learn more, see'
        ' https://docs.cloud.google.com/alloydb/docs/auth-proxy/connect#install.'
    )

    install_action = (
        'Please install the AlloyDB Auth Proxy with the following commands: '
    )
    post_install_action = (
        'mkdir -p ~/.local/bin\n'
        'mv alloydb-auth-proxy ~/.local/bin/\n'
        'export PATH="$HOME/.local/bin:$PATH"\n\n'
    )
    windows_post_install_action = (
        'New-Item -ItemType Directory -Force -Path "$HOME\\bin"\nMove-Item'
        ' -Path .\\alloydb-auth-proxy.exe -Destination "$HOME\\bin"\n$userPath'
        ' = [Environment]::GetEnvironmentVariable("Path",'
        ' "User")\n[Environment]::SetEnvironmentVariable("Path",'
        ' "$userPath;$HOME\\bin", "User")\n\n'
    )
    environment_setup_message = (
        'To persist these changes across sessions, add export'
        ' PATH="$HOME/.local/bin:$PATH" to your ~/.bashrc or ~/.zshrc file.\n'
    )
    if system == 'Linux' and machine == 'AMD64':
      action = (
          install_action
          + (
              '\n\nURL="https://storage.googleapis.com/alloydb-auth-proxy/v1.14.1"\nwget'
              ' "$URL/alloydb-auth-proxy.linux.amd64" -O'
              ' alloydb-auth-proxy\nchmod +x alloydb-auth-proxy\n'
          )
          + post_install_action
          + environment_setup_message
      )
    elif system == 'Linux' and machine == 'x86_64':
      action = (
          install_action
          + (
              '\n\nURL="https://storage.googleapis.com/alloydb-auth-proxy/v1.14.1"\nwget'
              ' "$URL/alloydb-auth-proxy.linux.amd64" -O'
              ' alloydb-auth-proxy\nchmod +x alloydb-auth-proxy\n'
          )
          + post_install_action
          + environment_setup_message
      )
    elif system == 'Linux' and machine == 'aarch64':
      action = (
          install_action
          + (
              '\n\nURL="https://storage.googleapis.com/alloydb-auth-proxy/v1.14.1"\nwget'
              ' "$URL/alloydb-auth-proxy.linux.arm64" -O'
              ' alloydb-auth-proxy\nchmod +x alloydb-auth-proxy\n'
          )
          + post_install_action
          + environment_setup_message
      )
    elif system == 'Linux' and machine == 'i386':
      action = (
          install_action
          + (
              '\n\nURL="https://storage.googleapis.com/alloydb-auth-proxy/v1.14.1"\nwget'
              ' "$URL/alloydb-auth-proxy.linux.386" -O'
              ' alloydb-auth-proxy\nchmod +x alloydb-auth-proxy\n'
          )
          + post_install_action
          + environment_setup_message
      )
    elif system == 'Darwin' and machine == 'arm64':
      action = (
          install_action
          + (
              '\n\nURL="https://storage.googleapis.com/alloydb-auth-proxy/v1.14.1"\nwget'
              ' "$URL/alloydb-auth-proxy.darwin.arm64" -O'
              ' alloydb-auth-proxy\nchmod +x alloydb-auth-proxy\n'
          )
          + post_install_action
          + environment_setup_message
      )
    elif system == 'Darwin' and machine in ['AMD64', 'x86_64']:
      action = (
          install_action
          + (
              '\n\nURL="https://storage.googleapis.com/alloydb-auth-proxy/v1.14.1"\nwget'
              ' "$URL/alloydb-auth-proxy.darwin.amd64" -O'
              ' alloydb-auth-proxy\nchmod +x alloydb-auth-proxy\n'
          )
          + post_install_action
          + environment_setup_message
      )
    elif system == 'Windows' and machine in ['AMD64', 'x86_64']:
      action = (
          install_action
          + (
              '\n\nInvoke-WebRequest -Uri'
              ' "https://storage.googleapis.com/alloydb-auth-proxy/v1.14.1/alloydb-auth-proxy-x64.exe"'
              ' -OutFile "alloydb-auth-proxy.exe"\n'
          )
          + windows_post_install_action
      )
    elif system == 'Windows' and machine == 'x86':
      action = (
          install_action
          + (
              '\n\nInvoke-WebRequest -Uri'
              ' "https://storage.googleapis.com/alloydb-auth-proxy/v1.14.1/alloydb-auth-proxy-x86.exe"'
              ' -OutFile "alloydb-auth-proxy.exe"\n'
          )
          + windows_post_install_action
      )

    super().__init__(error + action + learn_more)


class ProcessError(exceptions.Error):
  """Raise when a process fails to start."""


class Config:
  """Map gcloud CLI arguments to Auth Proxy and PSQL CLI arguments."""

  def __init__(
      self,
      cli_args,
      account,
      project,
      impersonate_service_account,
  ):
    self.account = account
    self.project = project
    self.impersonate_service_account = impersonate_service_account
    self.args = cli_args

  def ProxyCommand(self):
    """Return the AlloyDB Auth Proxy command based on the provided CLI args."""
    instance_uri = f'projects/{self.project}/locations/{self.args.region}/clusters/{self.args.cluster}/instances/{self.args.instance}'
    port = str(self.args.port)
    proxy_cmd = [AUTH_PROXY_BINARY, instance_uri, '--port', port]
    if getattr(self.args, 'psc', False):
      proxy_cmd.append('--psc')
    if getattr(self.args, 'public_ip', False):
      proxy_cmd.append('--public-ip')
    if getattr(self.args, 'auto_iam_authn', False):
      proxy_cmd.append('--auto-iam-authn')
    if self.impersonate_service_account:
      proxy_cmd += [
          '--impersonate-service-account',
          self.impersonate_service_account,
      ]
    return proxy_cmd

  def PsqlCommand(self):
    """Return the psql command based on the provided CLI args."""
    auto_iam_authn = getattr(self.args, 'auto_iam_authn', False)
    if auto_iam_authn:
      database_user = self.impersonate_service_account
      if not database_user:
        database_user = self.account
      if database_user.endswith('.gserviceaccount.com'):
        database_user = database_user.replace('.gserviceaccount.com', '')
    elif getattr(self.args, 'user', ''):
      database_user = self.args.user
    else:
      database_user = 'postgres'

    database = getattr(self.args, 'database', '')
    if not database:
      database = 'postgres'

    psql_cmd = [
        PSQL_BINARY,
        '-h',
        '127.0.0.1',
        '-p',
        str(self.args.port),
        '-U',
        database_user,
        '-d',
        database,
    ]
    return psql_cmd


class ProcessManager:
  """Manage subprocesses."""

  def __init__(self, process_wait_timeout=10, log_msg=log.status.write):
    self.process_wait_timeout = process_wait_timeout
    self.log_msg = log_msg

  def EnsureBinaryExists(self, binary, on_fail):
    path = files.FindExecutableOnPath(binary)
    if not path:
      raise on_fail
    return path

  @contextlib.contextmanager
  def StartBackgroundSubprocess(self, cmd):
    """Start a background subprocess.

    Args:
      cmd: The command to start

    Yields:
      The process, stdout path, and stderr path.
    """

    del self  # Unused
    process = None
    stdout_file = None
    stderr_file = None
    try:
      stdout_file = tempfile.NamedTemporaryFile(delete=False)
      stderr_file = tempfile.NamedTemporaryFile(delete=False)
      process = execution_utils.Subprocess(
          cmd,
          stdout=stdout_file,
          stdin=subprocess.PIPE,
          stderr=stderr_file,
          text=True,
      )
      yield process, stdout_file.name, stderr_file.name
    finally:
      if process and process.poll() is None:
        process.kill()
        try:
          process.wait(timeout=5)  # Wait a short time for it to terminate
        except subprocess.TimeoutExpired:
          pass  # Ignore timeout on cleanup
      if stdout_file:
        stdout_file.close()
        os.remove(stdout_file.name)
      if stderr_file:
        stderr_file.close()
        os.remove(stderr_file.name)

  def WaitForProcess(self, process, stdout_path, stderr_path, ready_msg):
    """Wait for the process to be ready.

    Args:
      process:     The process to wait for
      stdout_path: The path to the file where the process's stdout is sent
      stderr_path: The path to the file where the process's stderr is sent
      ready_msg:   The process stdout message that means the process is ready

    Raises:
      ProcessError: The Proxy could not start.
    """
    total_wait_seconds = 0
    seconds_to_sleep = 0.2
    with files.FileReader(stdout_path) as stdout_f:
      # poll returns None while process is running.
      while process.poll() is None:
        line = encoding.Decode(stdout_f.readline())
        if not line:  # EOF or process terminated
          if process.poll() is not None:
            break

        if ready_msg in line:
          return

        if total_wait_seconds >= self.process_wait_timeout:
          self.log_msg('Process failed to start: Timed out. Error log:\n')
          try:
            stdout = files.ReadFileContents(stdout_path)
            self.log_msg(f'\n\t{stdout}')
            stderr = files.ReadFileContents(stderr_path)
            self.log_msg(f'\t{stderr}\n')
          except FileNotFoundError:
            self.log_msg('\t(Failed to read stdout/stderr)\n')
          raise ProcessError('Failed to start the process: Timed out.')

        total_wait_seconds += seconds_to_sleep
        time.sleep(seconds_to_sleep)

    # Check if the process terminated unexpectedly
    if process.poll() is not None:
      self.log_msg('Process failed to start. Error log:\n')
      try:
        stdout = files.ReadFileContents(stdout_path)
        self.log_msg(f'\n\t{stdout}')
        stderr = files.ReadFileContents(stderr_path)
        self.log_msg(f'\t{stderr}\n')
      except FileNotFoundError:
        self.log_msg('\t(Failed to read stdout)\n')
      raise ProcessError(
          f'Process exited unexpectedly with code {process.poll()}.'
      )

  def Exec(self, cmd):
    return execution_utils.Exec(cmd)


def RunConnectCommand(config, process_manager, log_msg=log.status.write):
  """Connect to an AlloyDB instance using the AlloyDB Auth Proxy.

  Args:
    config:          The connect command configuration
    process_manager: An interface for starting processes
    log_msg:         The function to call to log output for the end-user

  Returns:
    If no exception is raised this method does not return. A new process is
    started and the original one is killed.
  Raises:
    PsqlNotFound:      The psql binary was not found
    AuthProxyNotFound: The Auth Proxy was not found
  """
  process_manager.EnsureBinaryExists(
      AUTH_PROXY_BINARY,
      AuthProxyNotFound(platform.system(), platform.machine()),
  )
  process_manager.EnsureBinaryExists(PSQL_BINARY, PsqlNotFound())

  log_msg('Starting the AlloyDB Auth Proxy...\n')
  log_msg('Running command:\n')
  proxy_cmd = config.ProxyCommand()
  proxy_cmd_line = ' '.join(proxy_cmd)
  log_msg(f'\t{proxy_cmd_line}\n')

  ready_msg = (
      'The proxy has started successfully and is ready for new connections!'
  )

  with process_manager.StartBackgroundSubprocess(proxy_cmd) as (
      process,
      stdout_path,
      stderr_path,
  ):
    process_manager.WaitForProcess(process, stdout_path, stderr_path, ready_msg)
    psql_cmd = config.PsqlCommand()

    try:
      log_msg('Connecting to the AlloyDB Auth Proxy...\n')
      log_msg('Running command:\n')
      psql_cmd_log = ' '.join(psql_cmd)
      log_msg(f'\t{psql_cmd_log}\n')
      process_manager.Exec(psql_cmd)
    except SystemExit as e:
      if e.code != 0:
        stdout = files.ReadFileContents(stdout_path)
        log_msg(f'Auth Proxy stdout:\n{stdout}\n')
        stderr = files.ReadFileContents(stderr_path)
        log_msg(f'Auth Proxy stderr:\n{stderr}\n')
        raise
