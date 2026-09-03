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
"""Helper class to stream/tail logs for Cloud Run dev sync."""

import re
import subprocess
import sys
import threading

from googlecloudsdk.command_lib.run.sync import ssh_util
from googlecloudsdk.core import log

_IGNORED_METADATA_PREFIXES = (
    'Project:',
    'Region:',
    'Instance:',
    'Revision:',
    'Container:',
    'Image:',
)

_LOG_LINE_PATTERN = re.compile(
    r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\s+'
    r'(\[[A-Za-z0-9_]+\])\s+\[[^\]]+\]\s*(.*)$'
)


class LogTailer:
  """Helper class to tail logs from a Cloud Run instance concurrently."""

  def __init__(self, ssh_session: ssh_util.MultiplexedSshSession):
    self._ssh_session = ssh_session
    self._process = None
    self._thread = None

  def _FilterAndStream(self):
    """Filters metadata header lines and streams container log output."""
    if not self._process or not self._process.stdout:
      return

    try:
      for line in iter(self._process.stdout.readline, ''):
        if any(
            line.startswith(prefix) for prefix in _IGNORED_METADATA_PREFIXES
        ):
          continue
        match = _LOG_LINE_PATTERN.match(line)
        if match:
          line = f'{match.group(1)} {match.group(2)}\n'
        sys.stdout.write(line)
        sys.stdout.flush()
    except Exception as e:  # pylint: disable=broad-except
      log.debug('Error in log tailer streaming thread: %s', e)

  def Start(self):
    """Starts the log tailing process in the background."""
    if self._process is not None:
      return

    try:
      ssh_cmd = self._ssh_session.GetSshCommand(
          remote_command=[
              '/lib64/ld-linux-x86-64.so.2',
              '/usr/local/gcp/bin/tail_logs',
          ]
      )

      cmd = ssh_cmd.Build(self._ssh_session.env)
      self._process = subprocess.Popen(
          cmd,
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
          text=True,
          bufsize=1,
      )
      self._thread = threading.Thread(
          target=self._FilterAndStream,
          daemon=True,
      )
      self._thread.start()
      log.debug('Started log tailing process PID %s', self._process.pid)
    except Exception as e:  # pylint: disable=broad-except
      log.warning('Failed to start log tailing: %s', e)
      self._process = None
      self._thread = None

  def Stop(self):
    """Stops the log tailing process if running."""
    if self._process is None:
      return

    try:
      log.debug('Stopping log tailing process PID %s', self._process.pid)
      self._process.terminate()
      self._process.wait(timeout=3)
    except Exception as e:  # pylint: disable=broad-except
      log.debug('Error stopping log tailing process: %s', e)
    finally:
      self._process = None
      self._thread = None
