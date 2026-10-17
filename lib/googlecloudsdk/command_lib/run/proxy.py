# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Wrapper for cloud-run-proxy binary."""


import functools
import subprocess
import threading

from googlecloudsdk.command_lib.config import config_helper
from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import store

MISSING_BINARY = ('Could not locate Cloud Run executable cloud-run-proxy'
                  ' on the system PATH. '
                  'Please ensure gcloud cloud-run-proxy component is properly '
                  'installed. '
                  'See https://cloud.google.com/sdk/docs/components for '
                  'more details.')
# Logs from the binary to be ignored.
IGNORED_LOGS = [' shutting down.', ' proxies to ']


class ProxyWrapper(binary_operations.StreamingBinaryBackedOperation):
  """Binary operation wrapper for cloud-run-proxy commands."""

  def __init__(self, **kwargs):
    super(ProxyWrapper, self).__init__(
        binary='cloud-run-proxy',
        custom_errors={'MISSING_EXEC': MISSING_BINARY},
        install_if_missing=True,
        std_err_func=StreamErrHandler,
        **kwargs)

  # Function required by StreamingBinaryBackedOperation to map command line args
  # from gcloud to the underlying component.
  def _ParseArgsForCommand(self,
                           host,
                           token=None,
                           bind=None,
                           duration=None,
                           **kwargs):
    del kwargs  # Not used here
    exec_args = ['-host', host]
    if token:
      exec_args.extend(['-token', token])
    if bind:
      exec_args.extend(['-bind', bind])
    if duration:
      exec_args.extend(['-server-up-time', duration])

    return exec_args


class BackgroundProxyWrapper(binary_operations.BinaryBackedOperation):
  """Binary operation wrapper for cloud-run-proxy on background threads.

  Uses BinaryBackedOperation instead of StreamingBinaryBackedOperation because
  the latter registers OS signal handlers that Python only permits on the main
  thread. _Execute is overridden to keep a handle to the running process so
  that Terminate() can stop it from another thread.
  """

  _TERMINATE_TIMEOUT_SECONDS = 5

  def __init__(self, port_flag='--proxy-port', **kwargs):
    super(BackgroundProxyWrapper, self).__init__(
        binary='cloud-run-proxy',
        custom_errors={'MISSING_EXEC': MISSING_BINARY},
        install_if_missing=True,
        std_err_func=functools.partial(StreamErrHandler, port_flag=port_flag),
        **kwargs,
    )
    # Guards _process and _terminated so that no process is started after
    # Terminate() has run.
    self._lock = threading.Lock()
    self._process = None
    self._terminated = False

  def _ParseArgsForCommand(
      self, host, token=None, bind=None, duration=None, **kwargs
  ):
    del kwargs  # Not used here
    exec_args = ['-host', host]
    if token:
      exec_args.extend(['-token', token])
    if bind:
      exec_args.extend(['-bind', bind])
    if duration:
      exec_args.extend(['-server-up-time', duration])

    return exec_args

  def _Execute(self, cmd, stdin=None, env=None, **kwargs):
    """Runs the proxy and streams its stderr until it exits.

    We override this because the base version gives us no way to stop the
    proxy once it starts. If parent command (like dev sync) crashes or exits
    without a KeyboardInterrupt, the proxy would keep running in the background
    and hold the local port. Here we keep a handle to the process so Terminate()
    can kill it.

    Args:
      cmd: [str], command to be executed with args.
      stdin: str, unused. The proxy doesn't read stdin.
      env: {str: str}, environment vars to send to binary.
      **kwargs: unused, accepted for compatibility with the base class.

    Returns:
      OperationResult: execution result for this invocation of the binary.
      Marked as failed without starting a process if Terminate() was called.
    """
    del stdin, kwargs  # Not used here
    result_holder = self.OperationResult(command_str=cmd)
    std_err_handler = self.std_err_handler(result_holder)
    with self._lock:
      if self._terminated:
        result_holder.failed = True
        return result_holder
      process = execution_utils.Subprocess(
          cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
      )
      self._process = process
    for line in iter(process.stderr.readline, b''):
      std_err_handler(line.decode('utf-8'))
    result_holder.exit_code = process.wait()
    self.set_failure_status(result_holder)
    return result_holder

  def Terminate(self):
    """Terminates the running proxy and prevents new ones from starting."""
    with self._lock:
      self._terminated = True
      process = self._process
    if process is None or process.poll() is not None:
      return
    process.terminate()
    try:
      process.wait(timeout=self._TERMINATE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
      process.kill()


def StreamErrHandler(result_holder, capture_output=False, port_flag='--port'):
  """Customized processing for streaming stderr from subprocess."""

  del result_holder, capture_output  # Unused

  def HandleStdErr(output):
    for line in output.splitlines():
      if any(to_be_ignored in line for to_be_ignored in IGNORED_LOGS):
        continue
      log.status.Print(line)
      # Check if it is bind used error
      if 'server error:' in line and 'bind: address already in use' in line:
        log.status.Print(
            'You can set the {} flag to specify a different local port'.format(
                port_flag
            )
        )

  return HandleStdErr


def GetFreshIdToken():
  """Returns an ID token for the active account."""
  cred = store.LoadFreshCredential()
  credential = config_helper.Credential(cred)
  return credential.id_token


class BackgroundProxy:
  """Runs the cloud-run-proxy refresh loop on a background thread."""

  def __init__(self, host, bind):
    """Initializes the background proxy.

    Args:
      host: str, the URL of the Cloud Run resource to proxy to.
      bind: str, the local address to bind to, e.g. '127.0.0.1:8080'.
    """
    self._host = host
    self._bind = bind
    # Constructed on the calling thread so that a missing component is prompted
    # for before anything is backgrounded.
    self._command_executor = BackgroundProxyWrapper()
    self._thread = None
    self._stopped = threading.Event()

  def _Run(self):
    """Keeps restarting the proxy with a fresh token until stopped."""
    try:
      # Keep restarting the proxy with fresh token before the token expires (1h)
      # until hitting a failure.
      while not self._stopped.is_set():
        response = self._command_executor(
            host=self._host,
            token=GetFreshIdToken(),
            bind=self._bind,
            duration='55m',
        )
        if response.failed:
          break
    except Exception as e:  # pylint: disable=broad-except
      # The command this proxy belongs to keeps running, so surface the failure
      # rather than letting the thread die silently.
      if not self._stopped.is_set():
        log.status.Print(f'Cloud Run proxy stopped: {e}')

  def Start(self):
    """Starts the proxy on a background thread."""
    self._thread = threading.Thread(target=self._Run, daemon=True)
    self._thread.start()

  def Stop(self):
    """Stops the refresh loop and terminates the running proxy process."""
    self._stopped.set()
    self._command_executor.Terminate()
